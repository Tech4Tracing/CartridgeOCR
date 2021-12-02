import { camera } from 'ionicons/icons';
import { IonContent, IonHeader, IonPage, IonTitle, IonToolbar,
  IonFab, IonFabButton, IonIcon, IonGrid, IonRow,
  IonCol, IonImg, IonActionSheet, IonCard, IonCardHeader,
  IonCardTitle, IonCardSubtitle, IonCardContent, IonListHeader } from '@ionic/react';
import { usePredictionApi } from '../hooks/usePredictionApi';
import './Predict.css';

const Predict: React.FC = () => {
  const { prediction, getPrediction } = usePredictionApi();
  return (
    <IonPage>
      <IonContent fullscreen>
        <IonCard>
          <IonCardHeader>
            <IonCardSubtitle>CartridgeOCR</IonCardSubtitle>
            <IonCardTitle>Get prediction results</IonCardTitle>
          </IonCardHeader>

          <IonCardContent>
            Upload an image to the prediction API to see the results. Click the camera button to take a photo & upload.
          </IonCardContent>
        </IonCard>

        <IonCard>
            <IonImg className='image' src={ prediction.webviewPath } />
        </IonCard>
        

        <IonFab vertical="bottom" horizontal="center" slot="fixed">
          <IonFabButton onClick={() => getPrediction()}>
            <IonIcon icon={camera}></IonIcon>
          </IonFabButton>
        </IonFab>

      </IonContent>
    </IonPage>
  );
};

export default Predict;
