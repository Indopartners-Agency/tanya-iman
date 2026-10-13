package id.tanyaiman.app;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup.MarginLayoutParams;
import android.webkit.WebView;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    private ConnectivityManager connectivity;
    private ConnectivityManager.NetworkCallback networkCallback;

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

        reportConnectivityToWebView(bridge.getWebView());
    }

    @Override
    public void onDestroy() {
        if (connectivity != null && networkCallback != null) {
            connectivity.unregisterNetworkCallback(networkCallback);
        }
        super.onDestroy();
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

    /**
     * Android's WebView does not watch the network itself: navigator.onLine
     * stays true in airplane mode and the online event never fires unless the
     * host app calls setNetworkAvailable. The chat resends a question that
     * failed offline on that event (Chat UX section 12), so without this the
     * seeker would have to tap Coba lagi by hand.
     */
    private void reportConnectivityToWebView(WebView webView) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return;

        connectivity = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
        if (connectivity == null) return;

        webView.setNetworkAvailable(connectivity.getActiveNetwork() != null);

        networkCallback = new ConnectivityManager.NetworkCallback() {
            @Override
            public void onAvailable(Network network) {
                runOnUiThread(() -> webView.setNetworkAvailable(true));
            }

            @Override
            public void onLost(Network network) {
                runOnUiThread(() -> webView.setNetworkAvailable(false));
            }
        };
        connectivity.registerDefaultNetworkCallback(networkCallback);
    }
}
