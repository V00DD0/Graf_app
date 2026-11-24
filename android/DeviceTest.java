package local.karta.qa;
import android.app.*;
import android.content.*;
import android.os.*;
import android.view.accessibility.AccessibilityNodeInfo;
import android.webkit.WebView;
import java.util.concurrent.*;

public class DeviceTest extends Instrumentation {
    private WebView web;
    private String mode;
    @Override public void onCreate(Bundle args){super.onCreate(args);mode=args.getString("mode","calls");start();}
    private String eval(String code) throws Exception{
        ArrayBlockingQueue<String> reply=new ArrayBlockingQueue<>(1);
        runOnMainSync(()->web.evaluateJavascript(code,value->reply.offer(value)));
        return reply.poll(5,TimeUnit.SECONDS);
    }
    private void await(String predicate) throws Exception {
        for(int i=0;i<80;i++){if("true".equals(eval(predicate)))return;Thread.sleep(250);}
        throw new AssertionError(predicate);
    }
    private boolean press(AccessibilityNodeInfo node,String label){
        if(node==null)return false;
        if(label.equalsIgnoreCase(node.getText()==null?"":node.getText().toString())){
            for(AccessibilityNodeInfo p=node;p!=null;p=p.getParent())
                if(p.isClickable())return p.performAction(AccessibilityNodeInfo.ACTION_CLICK);
        }
        for(int i=0;i<node.getChildCount();i++)if(press(node.getChild(i),label))return true;
        return false;
    }
    private void clickText(String label) throws Exception{
        for(int i=0;i<60;i++){if(press(getUiAutomation().getRootInActiveWindow(),label))return;Thread.sleep(250);}
        throw new AssertionError("Control unavailable: "+label);
    }
    private void waitForPicker() throws Exception{
        for(int i=0;i<100;i++){
            AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
            if(root!=null&&root.getPackageName()!=null&&root.getPackageName().toString().contains("contacts"))return;
            Thread.sleep(200);
        }
        throw new AssertionError("System contact picker did not appear");
    }
    private void waitForFiles() throws Exception{
        for(int i=0;i<100;i++){
            AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();
            if(root!=null&&root.getPackageName()!=null&&root.getPackageName().toString().contains("documentsui"))return;
            Thread.sleep(200);
        }
        throw new AssertionError("System file picker did not appear");
    }
    private void testBackup() throws Exception{
        String menu="document.querySelector('[data-act=more]').click();";
        eval(menu+"document.querySelector('[data-act=encrypted-export]').click()");
        await("!!document.querySelector('dialog')");
        eval("{const form=document.querySelector('dialog form');form.elements.secret.value='Backup7!';form.elements.confirmation.value='Backup7!';form.querySelector('[value=ok]').click()}");
        waitForFiles();clickText("Save");
        await("document.getElementById('kv2-toast').textContent.includes('сохранена и проверена')");
        eval("window.qaRestoreCancelled=false;const selectedBackup=window.kartaBackupSelected;window.kartaBackupSelected=(token)=>{window.qaRestoreCancelled=token===null;return selectedBackup(token)};document.querySelector('[data-act=import]').click()");
        waitForFiles();sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_BACK);
        await("window.qaRestoreCancelled===true");
        eval("document.querySelector('[data-act=import]').click()");
        waitForFiles();clickText("karta-svyazey-encrypted.json");
        await("document.querySelector('dialog')?.textContent.includes('Расшифровать резервную копию')===true");
        eval("{const form=document.querySelector('dialog form');form.elements.secret.value='Backup7!';form.querySelector('[value=ok]').click()}");
        clickText("OK");
        await("document.getElementById('kv2-toast').textContent.includes('Загружено')&&document.querySelector('svg').textContent.includes('Upgrade marker')");
    }
    @Override public void onStart(){
        Bundle out=new Bundle();
        try{
            Context app=getTargetContext();
            Intent intent=app.getPackageManager().getLaunchIntentForPackage(app.getPackageName());
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            Activity activity=startActivitySync(intent);
            runOnMainSync(()->web=(WebView)((android.view.ViewGroup)activity.findViewById(android.R.id.content)).getChildAt(0));
            await("!!document.querySelector('#kv2')&&!document.querySelector('#kv2').inert");
            await("typeof window.kartaPickedPhone===\u0027function\u0027 && typeof window.KartaFiles.analyzeCalls===\u0027function\u0027");
            if("seed".equals(mode)){
                eval("window.kartaPickedPhone('Upgrade marker','+12025550199',false)");
                await("document.querySelector('#kv2-side-body').innerText.includes('Upgrade marker')");
                Thread.sleep(650);
                out.putString("stream","PASS: upgrade seed");finish(Activity.RESULT_OK,out);return;
            }
            await("document.querySelector('svg').textContent.includes('Upgrade marker')");
            if("backup".equals(mode)){
                testBackup();
                out.putString("stream","PASS: SAF backup write, checksum, cancellation and AES-GCM restore");finish(Activity.RESULT_OK,out);return;
            }
            if("denied".equals(mode)){
                eval("window.qaCancelled=false;const oldCancel=window.kartaPickCancelled;window.kartaPickCancelled=()=>{oldCancel();window.qaCancelled=true};document.querySelector('[data-act=more]').click();document.querySelector('[data-act=pick-calls]').click()");
                waitForPicker();
                sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_BACK);
                await("window.qaCancelled===true");
                eval("document.querySelector('[data-act=pick-calls]').click()");
                eval("window.qaCancelTotal=false;const cancelTotals=window.kartaCallTotals;window.kartaCallTotals=(...a)=>{cancelTotals(...a);window.qaCancelTotal=a[1]===null}");
                waitForPicker();clickText("QA Contact");
                clickText("Отмена");await("window.qaCancelTotal===true");
                await("document.querySelector('svg').textContent.includes('QA Contact')");
            }
            eval("window.qaDenied=false;const oldTotals=window.kartaCallTotals;window.kartaCallTotals=(...a)=>{window.qaDenied=a[1]===null;oldTotals(...a)};document.querySelector('[data-act=group]').click();document.querySelector('[data-act=refresh-calls]').click()");
            if("denied".equals(mode)){
                clickText("Продолжить");
                await("window.qaDenied && document.querySelector('svg').textContent.includes('QA Contact') && !document.querySelector('[data-act=apply-group]')");
                out.putString("stream","PASS: picker cancel, consent cancel, permission denied, contact retained");finish(Activity.RESULT_OK,out);return;
            }
            clickText("Продолжить");
            await("!!document.querySelector('#accept-totals')");
            eval("document.querySelector('#accept-totals').click()");
            await("!!document.querySelector('[data-act=apply-group]')");
            eval("document.querySelector('[data-act=apply-group]').click()");
            await("!document.querySelector('[data-act=apply-group]')");
            String probe="(()=>{const open=indexedDB.open('karta-svyazey-2.1');open.onsuccess=()=>{const db=open.result;const q=db.transaction('graphs').objectStore('graphs').get('current');q.onsuccess=()=>{window.qaTotals=JSON.parse(q.result).people.find(p=>p.name==='QA Contact')?.calls?.count;db.close()}};return true})()";
            boolean match=false;
            for(int i=0;i<50&&!match;i++){eval(probe);Thread.sleep(200);match="2".equals(eval("window.qaTotals"));}
            if(!match)throw new AssertionError("Expected two answered calls, observed "+eval("window.qaTotals"));
            out.putString("stream","PASS: native consent, actual Android CallLog provider, answered-only 90-day count=2, preview, persistence");
            finish(Activity.RESULT_OK,out);
        }catch(Throwable t){out.putString("stream","FAIL: "+t.toString());finish(Activity.RESULT_CANCELED,out);}
    }
}
