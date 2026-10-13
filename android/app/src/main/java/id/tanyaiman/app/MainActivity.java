package id.tanyaiman.app;

import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup.MarginLayoutParams;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // From Android 15, targetSdk 35 apps are drawn edge-to-edge and
        // adjustResize no longer shrinks the window for the keyboard, so the
        // composer ends up underneath it (Chat UX section 12). Below 15 the
        // manifest's adjustResize still does the job on its own.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.VANILLA_ICE_CREAM) {
            fitWebViewToInsets(bridge.getWebView());
        }
    }

    /**
     * Keeps the WebView clear of the status bar, the navigation bar, display
     * cutouts and the keyboard by margining it inward. Capacitor's own
     * adjustMarginsForEdgeToEdge does the same but ignores the keyboard, so it
     * is disabled in capacitor.config.ts and this is the only inset handler.
     */
    private static void fitWebViewToInsets(View webView) {
        ViewCompat.setOnApplyWindowInsetsListener(webView, (v, windowInsets) -> {
            Insets bars = windowInsets.getInsets(
                WindowInsetsCompat.Type.systemBars() | WindowInsetsCompat.Type.displayCutout()
            );
            Insets ime = windowInsets.getInsets(WindowInsetsCompat.Type.ime());

            MarginLayoutParams mlp = (MarginLayoutParams) v.getLayoutParams();
            mlp.leftMargin = bars.left;
            mlp.topMargin = bars.top;
            mlp.rightMargin = bars.right;
            // The keyboard covers the navigation bar, so the larger one wins.
            mlp.bottomMargin = Math.max(bars.bottom, ime.bottom);
            v.setLayoutParams(mlp);

            return WindowInsetsCompat.CONSUMED;
        });
    }
}
