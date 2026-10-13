import type { CapacitorConfig } from '@capacitor/cli'

// F-39: the Android app is the same static build the web app and the widget
// serve. The native project sits at the repo root (PIP section 3), not inside
// web/app, so it is addressed by path here.
const config: CapacitorConfig = {
  appId: 'id.tanyaiman.app',
  appName: 'Tanya Iman',
  webDir: '.output/public',
  server: {
    // The WebView origin becomes https://localhost. The backend allows that
    // origin in CORS (deploy.sh), and no request is ever plain HTTP.
    androidScheme: 'https',
  },
  android: {
    path: '../../android',
    allowMixedContent: false,
    // Android 15 forces edge-to-edge for targetSdk 35. MainActivity.java owns
    // the insets instead, because Capacitor's margins ignore the keyboard and
    // would leave the composer underneath it.
    adjustMarginsForEdgeToEdge: 'disable',
  },
}

export default config
