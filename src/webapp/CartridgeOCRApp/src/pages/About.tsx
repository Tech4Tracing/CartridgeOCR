import { IonContent, IonHeader, IonPage, IonTitle, IonToolbar, 
         IonCard, IonCardHeader, IonCardTitle, IonCardSubtitle, 
         IonCardContent, IonListHeader, IonItem, IonList, IonIcon,
         IonLabel, IonButton } from '@ionic/react';
import { eye, pin } from 'ionicons/icons';
import './About.css';

const About: React.FC = () => {
  return (
    <IonPage>
      <IonContent fullscreen>

        <IonListHeader className="ion-margin-top">
          Overview
        </IonListHeader>
        
        <IonCard>
          <IonCardHeader>
            <IonCardSubtitle>UNIDIR</IonCardSubtitle>
            <IonCardTitle>CatridgeOCR</IonCardTitle>
          </IonCardHeader>

          <IonCardContent>
            This app helps investigators in conflict zones to catalog spent ammunition cartridges and track providence automatically
            through computer vision.
            <br />
            <br />
            <IonButton expand="block" href="https://onedrive.live.com/view.aspx?resid=EAAB78E2F796D3AF!976377&ithint=file%2cpptx&authkey=!AA2ATG4g_dT8ROk">Find out more</IonButton>
          </IonCardContent>
          
        </IonCard>

        <IonListHeader>
          Features
        </IonListHeader>
      
        <IonCard>
          <IonCardHeader>
            <IonCardTitle>Predict</IonCardTitle>
          </IonCardHeader>
          <IonCardContent>
            Take a photo of a cartidge and receive prediction results
          </IonCardContent>
        </IonCard>

        <IonCard>
          <IonCardHeader>
            <IonCardTitle>Upload</IonCardTitle>
          </IonCardHeader>
          <IonCardContent>
            Upload a photo of a cartidge for labelling to improve classification
          </IonCardContent>
        </IonCard>

      </IonContent>
    </IonPage>
  );
};

export default About;
