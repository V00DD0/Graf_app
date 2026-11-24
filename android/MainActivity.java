package local.karta.app;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.*;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.CallLog.Calls;
import android.provider.ContactsContract.Contacts;
import android.provider.ContactsContract.CommonDataKinds.Phone;
import android.telephony.PhoneNumberUtils;
import android.telephony.TelephonyManager;
import android.util.Base64;
import android.webkit.*;
import android.widget.Toast;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;

public final class MainActivity extends Activity {
    private static final String PAGE="https://appassets.androidplatform.net/index.html";
    private static final String BACKUP_URL="https://appassets.androidplatform.net/backup/";
    private static final String CONTACTS_URL="https://appassets.androidplatform.net/contacts";
    private static final int OPEN=1, SAVE=2, PICK=3, CALL_PERMISSION=4, OPEN_BACKUP=5, CONTACTS_PERMISSION=6;
    private static final long MAX_BACKUP_BYTES=128L*1024*1024;
    private WebView editor;
    private ValueCallback<Uri[]> chooser;
    private byte[] pendingDownload;
    private boolean verifyDownload, saving, choosingBackup;
    private final Object backupLock=new Object();
    private Uri backupUri;
    private String backupToken;
    private boolean countAfterPick;
    private boolean readingContacts;
    private final AtomicReference<byte[]> contactsResult=new AtomicReference<>();
    private String pendingToken, pendingRows;

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        editor=new WebView(this);
        editor.setOnApplyWindowInsetsListener((v,i)->{
            v.setPadding(i.getSystemWindowInsetLeft(),i.getSystemWindowInsetTop(),i.getSystemWindowInsetRight(),i.getSystemWindowInsetBottom());return i;
        });
        setContentView(editor);
        editor.getSettings().setJavaScriptEnabled(true);
        editor.getSettings().setDomStorageEnabled(true);
        editor.getSettings().setAllowFileAccess(false);
        editor.addJavascriptInterface(new Bridge(),"KartaFiles");
        editor.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest request){return !PAGE.equals(request.getUrl().toString());}
            @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest request){
                String url=request.getUrl().toString();
                if(PAGE.equals(url))try{return new WebResourceResponse("text/html","UTF-8",getAssets().open("index.html"));}catch(IOException ignored){}
                if("GET".equals(request.getMethod())&&url.startsWith(BACKUP_URL))return readBackup(url.substring(BACKUP_URL.length()));
                if("GET".equals(request.getMethod())&&CONTACTS_URL.equals(url)){
                    byte[] result=contactsResult.getAndSet(null);
                    if(result!=null)return new WebResourceResponse("application/json","UTF-8",200,"OK",
                        Collections.singletonMap("Cache-Control","no-store"),new ByteArrayInputStream(result));
                }
                return new WebResourceResponse("text/plain","UTF-8",new ByteArrayInputStream(new byte[0]));
            }
        });
        editor.setWebChromeClient(new WebChromeClient(){
            @Override public boolean onJsConfirm(WebView v,String url,String text,JsResult result){
                new AlertDialog.Builder(MainActivity.this).setMessage(text)
                    .setNegativeButton("Отмена",(dialog,which)->result.cancel())
                    .setOnCancelListener(dialog->result.cancel())
                    .setPositiveButton("Подтвердить",(dialog,which)->result.confirm()).show();
                return true;
            }
            @Override public boolean onShowFileChooser(WebView v,ValueCallback<Uri[]> callback,FileChooserParams params){
                if(chooser!=null)chooser.onReceiveValue(null);
                chooser=callback;
                try{startActivityForResult(params.createIntent(),OPEN);}catch(RuntimeException e){chooser.onReceiveValue(null);chooser=null;message("Выбор файла недоступен");}
                return true;
            }
        });
        editor.loadUrl(PAGE);
    }
    private void message(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
    private void js(String script){if(!isDestroyed()&&PAGE.equals(editor.getUrl()))editor.evaluateJavascript(script,null);}
    public final class Bridge {
        @JavascriptInterface public String normalizePhone(String number){return canonical(number,phoneRegion());}
        @JavascriptInterface public void openBackup(){
            runOnUiThread(()->{
                if(choosingBackup)return;
                choosingBackup=true;
                try{
                    startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
                        .setType("*/*"),OPEN_BACKUP);
                }catch(RuntimeException e){
                    choosingBackup=false;
                    js("window.kartaBackupSelected(null)");
                    message("Выбор файла недоступен");
                }
            });
        }
        @JavascriptInterface public void pickPhone(boolean withCalls){
            runOnUiThread(()->{
                countAfterPick=withCalls;
                try{startActivityForResult(new Intent(Intent.ACTION_PICK,Phone.CONTENT_URI),PICK);}
                catch(RuntimeException e){js("window.kartaPickCancelled()");message("Приложение контактов недоступно");}
            });
        }
        @JavascriptInterface public void pickContacts(){
            runOnUiThread(()->{
                if(readingContacts)return;
                readingContacts=true;
                if(checkSelfPermission(Manifest.permission.READ_CONTACTS)==PackageManager.PERMISSION_GRANTED)readContacts();
                else try{requestPermissions(new String[]{Manifest.permission.READ_CONTACTS},CONTACTS_PERMISSION);}
                catch(SecurityException e){finishContacts(null,"Не удалось запросить доступ к контактам");}
            });
        }
        @JavascriptInterface public void analyzeCalls(String token,String rows){
            if(rows==null||rows.length()>2000000||token==null||token.length()>150)return;
            runOnUiThread(()->{
                if(pendingToken!=null){js("window.kartaCallTotals("+JSONObject.quote(token)+",null)");message("Уже идёт чтение журнала");return;}
                pendingToken=token;pendingRows=rows;
                new AlertDialog.Builder(MainActivity.this).setTitle("Учесть звонки за 90 дней?")
                    .setMessage("Будут подсчитаны входящие и исходящие вызовы с длительностью больше нуля для выбранных номеров. В карточках сохраняются итоги и дата обновления. После расчёта вы увидите предпросмотр.")
                    .setNegativeButton("Отмена",(d,w)->finishCounts(null))
                    .setOnCancelListener(d->finishCounts(null))
                    .setPositiveButton("Продолжить",(d,w)->{
                        if(checkSelfPermission(Manifest.permission.READ_CALL_LOG)==PackageManager.PERMISSION_GRANTED)readCounts();
                        else try{requestPermissions(new String[]{Manifest.permission.READ_CALL_LOG},CALL_PERMISSION);}
                        catch(SecurityException e){denyCounts();}
                    }).show();
            });
        }
        @JavascriptInterface public void save(String name,String type,String text,boolean encoded){
            runOnUiThread(()->{
                if(saving){message("Завершите сохранение");return;}
                try{
                    pendingDownload=encoded?Base64.decode(text,Base64.DEFAULT):text.getBytes(StandardCharsets.UTF_8);
                    verifyDownload="karta-svyazey-encrypted.json".equals(name);
                    saving=true;
                    startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
                       .setType(type.split(";")[0]).putExtra(Intent.EXTRA_TITLE,name),SAVE);
                }catch(RuntimeException e){pendingDownload=null;saving=false;message("Ошибка сохранения");}
            });
        }
    }
    private WebResourceResponse readBackup(String token){
        Uri uri;
        synchronized(backupLock){
            uri=token.equals(backupToken)?backupUri:null;
            if(uri!=null){backupToken=null;backupUri=null;}
        }
        Map<String,String> headers=Collections.singletonMap("Cache-Control","no-store");
        if(uri!=null)try{
            InputStream source=getContentResolver().openInputStream(uri);
            if(source!=null){
                InputStream limited=new FilterInputStream(source){
                    private long size;
                    private int count(int bytes) throws IOException{
                        if(bytes>0&&(size+=bytes)>MAX_BACKUP_BYTES)throw new IOException("Backup exceeds size limit");
                        return bytes;
                    }
                    @Override public int read() throws IOException{
                        int value=in.read();
                        if(value!=-1)count(1);
                        return value;
                    }
                    @Override public int read(byte[] buffer,int offset,int length) throws IOException{
                        return count(in.read(buffer,offset,length));
                    }
                };
                return new WebResourceResponse("application/json","UTF-8",200,"OK",headers,limited);
            }
        }catch(IOException|RuntimeException ignored){}
        return new WebResourceResponse("text/plain","UTF-8",404,"Not Found",headers,new ByteArrayInputStream(new byte[0]));
    }
    private void saveDocument(Uri uri,byte[] bytes,boolean verify){
        String result;
        try{
            try(OutputStream out=getContentResolver().openOutputStream(uri,"wt")){
                if(out==null)throw new IOException();
                out.write(bytes);
            }
            if(verify){
                MessageDigest digest=MessageDigest.getInstance("SHA-256");
                byte[] expected=digest.digest(bytes),buffer=new byte[32*1024];
                long count=0;
                try(InputStream in=getContentResolver().openInputStream(uri)){
                    if(in==null)throw new IOException();
                    for(int length;(length=in.read(buffer))!=-1;){
                        count+=length;
                        if(count>bytes.length)throw new IOException();
                        digest.update(buffer,0,length);
                    }
                }
                if(count!=bytes.length||!MessageDigest.isEqual(expected,digest.digest()))throw new IOException();
            }
            result=verify?"Резервная копия сохранена и проверена":"Файл сохранён";
        }catch(Exception e){result=verify?"Не удалось сохранить или проверить резервную копию":"Ошибка записи";}
        String text=result;
        runOnUiThread(()->{
            saving=false;
            if(isDestroyed())return;
            if(verify)js("window.kartaBackupSaved("+JSONObject.quote(text)+")");
            else message(text);
        });
    }
    private void finishCounts(JSONObject result){finishCounts(result,null,null);}
    private void finishCounts(JSONObject result,String start,String end){
        if(pendingToken!=null)js("window.kartaCallTotals("+JSONObject.quote(pendingToken)+","+(result==null?"null":result.toString())+","+JSONObject.quote(start)+","+JSONObject.quote(end)+")");
        pendingRows=null;pendingToken=null;
    }
    private void denyCounts(){message("Журнал недоступен. Контакт сохранён, если был добавлен. Итоги можно импортировать в разделе группировки.");finishCounts(null);}
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] results){
        super.onRequestPermissionsResult(request,permissions,results);
        if(request==CALL_PERMISSION&&pendingToken!=null){
            if(results.length>0&&results[0]==PackageManager.PERMISSION_GRANTED)readCounts();else denyCounts();
        }else if(request==CONTACTS_PERMISSION&&readingContacts){
            if(results.length>0&&results[0]==PackageManager.PERMISSION_GRANTED)readContacts();
            else finishContacts(null,"Для массового выбора нужен доступ к контактам. Можно добавить один контакт через системный выбор.");
        }
    }
    private void finishContacts(byte[] result,String error){
        readingContacts=false;
        if(isDestroyed()||isFinishing())return;
        contactsResult.set(result);
        js("window.kartaContactsReady("+(error==null?"null":JSONObject.quote(error))+")");
    }
    private void readContacts(){
        new Thread(()->{
            try{
                ContentResolver resolver=getContentResolver();
                String region=phoneRegion();
                Map<Long,String> phones=new HashMap<>();
                // Prefer the contact's default number, then the first valid number by ID.
                try(Cursor rows=resolver.query(Phone.CONTENT_URI,new String[]{Phone.CONTACT_ID,Phone.NUMBER},null,null,
                        Phone.IS_SUPER_PRIMARY+" DESC, "+Phone.IS_PRIMARY+" DESC, "+Phone._ID+" ASC")){
                    if(rows==null)throw new IOException();
                    while(rows.moveToNext()){
                        long id=rows.getLong(0);
                        if(phones.containsKey(id))continue;
                        String number=canonical(rows.getString(1),region);
                        if(!number.isEmpty())phones.put(id,number);
                    }
                }
                JSONArray contacts=new JSONArray();
                try(Cursor rows=resolver.query(Contacts.CONTENT_URI,new String[]{Contacts._ID,Contacts.DISPLAY_NAME_PRIMARY},null,null,
                        Contacts.DISPLAY_NAME_PRIMARY+" COLLATE LOCALIZED ASC, "+Contacts._ID+" ASC")){
                    if(rows==null)throw new IOException();
                    while(rows.moveToNext()){
                        String name=rows.getString(1),phone=phones.getOrDefault(rows.getLong(0),"");
                        if(name==null)name="";
                        if(!name.trim().isEmpty()||!phone.isEmpty())contacts.put(new JSONObject()
                            .put("name",name.substring(0,Math.min(256,name.length()))).put("phone",phone));
                    }
                }
                byte[] result=contacts.toString().getBytes(StandardCharsets.UTF_8);
                runOnUiThread(()->finishContacts(result,null));
            }catch(Exception e){runOnUiThread(()->finishContacts(null,"Не удалось прочитать телефонную книгу"));}
        }).start();
    }
    private String phoneRegion(){
        TelephonyManager tel=(TelephonyManager)getSystemService(TELEPHONY_SERVICE);
        String region=tel==null?"":tel.getNetworkCountryIso();
        if(region==null||region.isEmpty())region=Locale.getDefault().getCountry();
        return region.toUpperCase(Locale.US);
    }
    private String canonical(String number,String region){
        if(number==null)return "";
        String raw=PhoneNumberUtils.normalizeNumber(number);
        if(raw.startsWith("00"))raw="+"+raw.substring(2);
        if(!raw.matches("\\+?[0-9]{5,15}"))return "";
        String international=PhoneNumberUtils.formatNumberToE164(raw,region);
        return international==null?raw:international;
    }
    private void readCounts(){
        final String snapshot=pendingRows;
        if(snapshot==null)return;
        new Thread(()->{
            try{
                String region=phoneRegion();
                Map<String,String> ids=new HashMap<>();Set<String> shared=new HashSet<>();
                JSONArray rows=new JSONArray(snapshot);JSONObject counts=new JSONObject();
                for(int i=0;i<rows.length();i++){
                    JSONObject row=rows.getJSONObject(i);
                    String number=canonical(row.getString("phone"),region);
                    if(number.isEmpty())continue;
                    if(ids.containsKey(number))shared.add(number);
                    ids.put(number,row.getString("id"));
                }
                for(String number:shared)ids.remove(number);
                for(String id:ids.values())counts.put(id,0);
                long now=System.currentTimeMillis();
                String where=Calls.DATE+" BETWEEN ? AND ? AND "+Calls.DURATION+">0 AND "+Calls.TYPE+" IN (?,?)";
                String[] args={String.valueOf(now-90L*86400000),String.valueOf(now),String.valueOf(Calls.INCOMING_TYPE),String.valueOf(Calls.OUTGOING_TYPE)};
                try(Cursor c=getContentResolver().query(Calls.CONTENT_URI,new String[]{Calls.NUMBER},where,args,null)){
                    if(c==null)throw new IOException();
                    while(c.moveToNext()){
                        String id=ids.get(canonical(c.getString(0),region));
                        if(id!=null)counts.put(id,counts.getInt(id)+1);
                    }
                }
                java.time.ZoneId zone=java.time.ZoneId.systemDefault();
                String start=java.time.Instant.ofEpochMilli(now-90L*86400000).atZone(zone).toLocalDate().toString();
                String end=java.time.Instant.ofEpochMilli(now).atZone(zone).toLocalDate().toString();
                runOnUiThread(()->finishCounts(counts,start,end));
            }catch(Exception e){runOnUiThread(()->denyCounts());}
        }).start();
    }
    @Override protected void onActivityResult(int request,int result,Intent reply){
        super.onActivityResult(request,result,reply);
        Uri uri=result==RESULT_OK&&reply!=null?reply.getData():null;
        if(request==PICK&&uri!=null&&"content".equals(uri.getScheme())){
            try(Cursor c=getContentResolver().query(uri,new String[]{Phone.DISPLAY_NAME,Phone.NUMBER},null,null,null)){
                if(c!=null&&c.moveToFirst()&&c.getString(1)!=null)
                    js("window.kartaPickedPhone("+JSONObject.quote(c.getString(0))+","+JSONObject.quote(c.getString(1))+","+countAfterPick+")");
                else js("window.kartaPickCancelled()");
            }catch(RuntimeException e){js("window.kartaPickCancelled()");message("Не удалось прочитать выбранный номер");}
        }else if(request==PICK){js("window.kartaPickCancelled()");
        }else if(request==OPEN&&chooser!=null){
            Uri[] files=WebChromeClient.FileChooserParams.parseResult(result,reply);
            if(files!=null)for(Uri f:files)if(!"content".equals(f.getScheme())){files=null;break;}
            chooser.onReceiveValue(files);chooser=null;
        }else if(request==OPEN_BACKUP){
            choosingBackup=false;
            String token=null;
            synchronized(backupLock){
                backupUri=uri!=null&&"content".equals(uri.getScheme())?uri:null;
                backupToken=backupUri==null?null:UUID.randomUUID().toString();
                token=backupToken;
            }
            js("window.kartaBackupSelected("+(token==null?"null":JSONObject.quote(token))+")");
        }else if(request==SAVE){
            byte[] bytes=pendingDownload;pendingDownload=null;
            if(uri==null||!"content".equals(uri.getScheme())){saving=false;return;}
            if(bytes==null){saving=false;message("Повторите экспорт");return;}
            boolean verify=verifyDownload;
            new Thread(()->saveDocument(uri,bytes,verify)).start();
        }
    }
}
