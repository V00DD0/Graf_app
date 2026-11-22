package local.karta.qa;
import android.app.*;
import android.content.*;
import android.os.*;
import android.view.accessibility.AccessibilityNodeInfo;
import android.webkit.WebView;
import java.util.concurrent.*;

public class DeviceTest extends Instrumentation {
    private WebView web;
    @Override public void onCreate(Bundle args){super.onCreate(args);start();}
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
        if(label.equalsIgnoreCase(node.getText()==null?"":node.getText().toString())&&node.isClickable())
            return node.performAction(AccessibilityNodeInfo.ACTION_CLICK);
        for(int i=0;i<node.getChildCount();i++)if(press(node.getChild(i),label))return true;
        return false;
    }
    private void describe(AccessibilityNodeInfo n,StringBuilder text){
        if(n==null||text.length()>1000)return;
        if(n.getText()!=null)text.append(n.getText()).append("|");
        for(int i=0;i<n.getChildCount();i++)describe(n.getChild(i),text);
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
            eval("window.kartaPickedPhone('Проверка','+12025550137',true)");
            boolean clicked=false;
            for(int i=0;i<60&&!clicked;i++){clicked=press(getUiAutomation().getRootInActiveWindow(),"Продолжить");Thread.sleep(250);}
            if(!clicked){
                StringBuilder visible=new StringBuilder();
                describe(getUiAutomation().getRootInActiveWindow(),visible);
                throw new AssertionError("Consent button unavailable. UI="+visible+" editor="+eval("document.body.innerText.slice(-400)"));
            }
            await("!!document.querySelector('[data-act=apply-group]')");
            eval("document.querySelector('[data-act=apply-group]').click()");
            await("!document.querySelector('[data-act=apply-group]')");
            String probe="(()=>{const open=indexedDB.open('karta-svyazey-2.1');open.onsuccess=()=>{const db=open.result;const q=db.transaction('graphs').objectStore('graphs').get('current');q.onsuccess=()=>{window.qaTotals=JSON.parse(q.result).people[0]?.calls?.count;db.close()}};return true})()";
            boolean match=false;
            for(int i=0;i<50&&!match;i++){eval(probe);Thread.sleep(200);match="2".equals(eval("window.qaTotals"));}
            if(!match)throw new AssertionError("Expected two answered calls, observed "+eval("window.qaTotals"));
            out.putString("stream","PASS: native consent, actual Android CallLog provider, answered-only 90-day count=2, preview, persistence");
            finish(Activity.RESULT_OK,out);
        }catch(Throwable t){out.putString("stream","FAIL: "+t.toString());finish(Activity.RESULT_CANCELED,out);}
    }
}