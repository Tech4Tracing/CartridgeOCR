import { useState } from "react";
import { base64FromPath } from '@ionic/react-hooks/filesystem';
import config from "../appConfig.json";
import { Photo } from "./useDeviceCamera";
import { isPlatform } from '@ionic/react';
import { CameraResultType, CameraSource, CameraPhoto, Capacitor, FilesystemDirectory, Filesystem, Storage, Camera } from "@capacitor/core";
import { useCamera } from '@ionic/react-hooks/camera';

export function usePredictionApi() {
    const { getPhoto } = useCamera();
    const [prediction, setPrediction] = useState<Photo>({ filepath: "" });

    const getPrediction = async () => {
        const photo = await takePhoto();
        console.log("took a pic!");
        const base64photo = await convertToBase64(photo);
        console.log(base64photo);
        const base64prediction = await predict(base64photo);
        console.log(base64prediction);

        const fileName = "prediction" + new Date().getTime() + '.jpeg';
        const prediction = convertToImage(base64prediction, fileName);
        setPrediction(prediction);
    }

    const takePhoto = async () => {
        const cameraPhoto = await getPhoto({
            resultType: CameraResultType.Uri,
            source: CameraSource.Camera,
            quality: 100
          });

        return cameraPhoto;
    };

    const convertToBase64 = async (photo: CameraPhoto) => {
        let base64Data: string;
        
        if (isPlatform('hybrid')) {
            const file = await Filesystem.readFile({
                path: photo.path!
            });
            base64Data = file.data;
        } else {
            base64Data = await base64FromPath(photo.webPath!);
        }

        // As the base64 string contains the filetype metadata at the start, we should split it out
        const base64Items = base64Data.split(",", 2);
        // // And trim the "data:" from the start to get the fileType
        // const fileType = base64Items[0].replace('data:','');

        return base64Items[1];
    };

    const predict = async (base64Image: string) => {
        const predictAPIURI = config.predictAPIURI;

        const body = { image: base64Image }
        console.log(body);

        // Call the prediction API
        try {
            const res = await fetch(
                predictAPIURI, {
                method: "POST",
                body: JSON.stringify(body),
                headers: new Headers({
                    //'Authorization': 'Bearer ' + idToken,
                    'Content-Type': 'application/json'
                })
            });
            return await res.json();
        } catch (error) {
            // Handle errors posting to API
            console.error("Error calling upload API: ", error);
        }
    };

    const convertToImage = (base64Image: string, filepath: string) => {
        return {
            filepath,
            webviewPath: `data:image/jpeg;base64,${base64Image}`
        }
    };

    return {
        prediction,
        getPrediction
    };
}