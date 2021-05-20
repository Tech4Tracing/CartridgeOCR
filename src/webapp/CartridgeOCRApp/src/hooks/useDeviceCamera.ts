import { useState, useEffect } from "react";
import { useCamera } from '@ionic/react-hooks/camera';
import { base64FromPath } from '@ionic/react-hooks/filesystem';
import { isPlatform } from '@ionic/react';
import { CameraResultType, CameraSource, CameraPhoto, Capacitor, FilesystemDirectory, Filesystem, Storage } from "@capacitor/core";

export interface Photo {
  filepath: string;
  webviewPath?: string;
}

const PHOTO_STORAGE = "photos";

export function useDeviceCamera() {
 
    // Use the ionic camera hook
    const { getPhoto } = useCamera();
    const [photos, setPhotos] = useState<Photo[]>([]);

    useEffect(() => {
      const loadSaved = async () => {
        const {value} = await Storage.get({key: PHOTO_STORAGE });
        const photosInStorage = (value ? JSON.parse(value) : []) as Photo[];
    
        // If running on the web...
        if (!isPlatform('hybrid')) {
          for (let photo of photosInStorage) {
            const file = await Filesystem.readFile({
              path: photo.filepath,
              directory: FilesystemDirectory.Data
            });
            // Web platform only: Load the photo as base64 data
            photo.webviewPath = `data:image/jpeg;base64,${file.data}`;
          }
        }

        setPhotos(photosInStorage);
      };
      loadSaved();
    }, []);
  
    // Method to take a photo with a device camera
    const takePhoto = async () => {

      // Call capacitor API to take photo (device agnostic)
      const cameraPhoto = await getPhoto({
        resultType: CameraResultType.Uri,
        source: CameraSource.Camera,
        quality: 100
      });

      // Name the created file
      const fileName = new Date().getTime() + '.jpeg';

      // Call savePicture() to persist photo to local filesystem
      const savedFileImage = await savePicture(cameraPhoto, fileName);
      
      // Update state with new photo(s)
      const newPhotos = [savedFileImage, ...photos];
      setPhotos(newPhotos)
      Storage.set({key: PHOTO_STORAGE,value: JSON.stringify(newPhotos)});
    };

    // Method to persist photos to device storage
    const savePicture = async (photo: CameraPhoto, fileName: string): Promise<Photo> => {
      let base64Data: string;

      // "hybrid" will detect Cordova or Capacitor;
      if (isPlatform('hybrid')) {
        const file = await Filesystem.readFile({
          path: photo.path!
        });
        base64Data = file.data;
      } else {
        base64Data = await base64FromPath(photo.webPath!);
      }

      const savedFile = await Filesystem.writeFile({
        path: fileName,
        data: base64Data,
        directory: FilesystemDirectory.Data
      });

      if (isPlatform('hybrid')) {
        // Display the new image by rewriting the 'file://' path to HTTP
        // Details: https://ionicframework.com/docs/building/webview#file-protocol
        return {
          filepath: savedFile.uri,
          webviewPath: Capacitor.convertFileSrc(savedFile.uri),
        };
      }
      else {
        // Use webPath to display the new image instead of base64 since it's
        // already loaded into memory
        return {
          filepath: fileName,
          webviewPath: photo.webPath
        };
      }
    };

    return {
      photos,
      takePhoto
    };
}