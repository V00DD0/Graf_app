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
import android.provider.ContactsContract.CommonDataKinds.Phone;
import android.telephony.PhoneNumberUtils;
import android.telephony.TelephonyManager;
import android.util.Base64;
import android.webkit.*;
import android.widget.Toast;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public final class MainActivity extends Activity {
    private static final String PAGE="https://appassets.androidplatform.net/index.html";
    private static final int OPEN=1, SAVE=2, PICK=3, CALL_PERMISSION=4;
    private WebView editor;
    private ValueCallback<Uri[]> chooser;
    private byte[] pendingDownload;
    private boolean countAfterPick;
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
                if(PAGE.equals(request.getUrl().toString()))try{return new WebResourceResponse("text/html","UTF-8",getAssets().open("index.html"));}catch(IOException ignored){}
                return new WebResourceResponse("text/plain","UTF-8",new ByteArrayInputStream(new byte[0]));
            }
        });
        editor.setWebChromeClient(new WebChromeClient(){
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
        @JavascriptInterface public void pickPhone(boolean withCalls){
            runOnUiThread(()->{
                countAfterPick=withCalls;
                try{startActivityForResult(new Intent(Intent.ACTION_PICK,Phone.CONTENT_URI),PICK);}
                catch(RuntimeException e){js("window.kartaPickCancelled()");message("Приложение контактов недоступно");}
            });
        }
        @JavascriptInterface public void analyzeCalls(String token,String rows){
            if(rows==null||rows.length()>2000000||token==null||token.length()>150)return;
            runOnUiThread(()->{
                if(pendingToken!=null){js("window.kartaCallTotals("+JSONObject.quote(token)+",null)");message("Уже идёт чтение журнала");return;}
                pendingToken=token;pendingRows=rows;
                new AlertDialog.Builder(MainActivity.this).setTitle("Учесть звонки за 90 дней?")
                    .setMessage("Будут подсчитаны входящие и исходящие вызовы с длительностью больше нуля для номеров на карте. В карточках и экспорте сохраняются только итоги и дата обновления. После расчёта вы увидите предпросмотр.")
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
                if(pendingDownload!=null){message("Завершите сохранение");return;}
                try{
                    pendingDownload=encoded?Base64.decode(text,Base64.DEFAULT):text.getBytes(StandardCharsets.UTF_8);
                    startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
                       .setType(type.split(";")[0]).putExtra(Intent.EXTRA_TITLE,name),SAVE);
                }catch(RuntimeException e){pendingDownload=null;message("Ошибка сохранения");}
            });
        }
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
        }
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
        }else if(request==SAVE){
            byte[] bytes=pendingDownload;pendingDownload=null;
            if(uri==null)return;
            if(bytes==null){message("Повторите экспорт");return;}
            new Thread(()->{
                try(OutputStream out=getContentResolver().openOutputStream(uri,"wt")){
                    if(out==null)throw new IOException();out.write(bytes);
                }catch(Exception e){runOnUiThread(()->message("Ошибка записи"));return;}
                runOnUiThread(()->message("Файл сохранён"));
            }).start();
        }
    }
}