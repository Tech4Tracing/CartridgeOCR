import { camera } from 'ionicons/icons';
import { IonContent, IonHeader, IonPage, IonTitle, IonToolbar,
         IonFab, IonFabButton, IonIcon, IonGrid, IonRow,
         IonCol, IonImg, IonActionSheet, IonCard, IonCardHeader,
         IonCardTitle, IonCardSubtitle, IonCardContent, IonListHeader } from '@ionic/react';
import { useDeviceCamera } from '../hooks/useDeviceCamera';
import './Upload.css';

const Upload: React.FC = () => {
  const { photos, takePhoto } = useDeviceCamera();
  return (
    <IonPage>
      <IonContent fullscreen>
        <IonCard>
          <IonCardHeader>
            <IonCardSubtitle>CartridgeOCR</IonCardSubtitle>
            <IonCardTitle>Upload training images</IonCardTitle>
          </IonCardHeader>

          <IonCardContent>
            Upload images to the training API to improve label classification. Click the camera button to take a photo & upload.
          </IonCardContent>
        </IonCard>

        <IonListHeader>
          Uploads
        </IonListHeader>

        <IonGrid>
          <IonRow>
            {photos.map((photo, index) => (
              <IonCol size="6" key={index}>
                <IonImg src={photo.webviewPath} />
              </IonCol>
            ))}
          </IonRow>
        </IonGrid>
        
        <IonFab vertical="bottom" horizontal="center" slot="fixed">
          <IonFabButton onClick={() => takePhoto()}>
            <IonIcon icon={camera}></IonIcon>
          </IonFabButton>
        </IonFab>

      </IonContent>
    </IonPage>
  );
};

export default Upload;
