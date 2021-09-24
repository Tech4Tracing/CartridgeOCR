import { Redirect, Route } from 'react-router-dom';
import {
  IonApp,
  IonIcon,
  IonLabel,
  IonRouterOutlet,
  IonTabBar,
  IonTabButton,
  IonTabs,
} from '@ionic/react';
import { IonReactRouter } from '@ionic/react-router';
import { camera, eye, informationCircle } from 'ionicons/icons';
import Predict from './pages/Predict';
import Upload from './pages/Upload';
import About from './pages/About';

/* Core CSS required for Ionic components to work properly */
import '@ionic/react/css/core.css';

/* Basic CSS for apps built with Ionic */
import '@ionic/react/css/normalize.css';
import '@ionic/react/css/structure.css';
import '@ionic/react/css/typography.css';

/* Optional CSS utils that can be commented out */
import '@ionic/react/css/padding.css';
import '@ionic/react/css/float-elements.css';
import '@ionic/react/css/text-alignment.css';
import '@ionic/react/css/text-transformation.css';
import '@ionic/react/css/flex-utils.css';
import '@ionic/react/css/display.css';

/* Theme variables */
import './theme/variables.css';

const App: React.FC = () => (
  <IonApp>
    <IonReactRouter>
      <IonTabs>
        <IonRouterOutlet>
          <Route exact path="/predict">
            <Predict />
          </Route>
          <Route exact path="/upload">
            <Upload />
          </Route>
          <Route path="/about">
            <About />
          </Route>
          <Route exact path="/">
            <Redirect to="/predict" />
          </Route>
        </IonRouterOutlet>
        <IonTabBar slot="bottom">
          <IonTabButton tab="predict" href="/predict">
            <IonIcon icon={eye} />
            <IonLabel>Predict</IonLabel>
          </IonTabButton>
          <IonTabButton tab="upload" href="/upload">
            <IonIcon icon={camera} />
            <IonLabel>Upload</IonLabel>
          </IonTabButton>
          <IonTabButton tab="about" href="/about">
            <IonIcon icon={informationCircle} />
            <IonLabel>About</IonLabel>
          </IonTabButton>
        </IonTabBar>
      </IonTabs>
    </IonReactRouter>
  </IonApp>
);

export default App;
