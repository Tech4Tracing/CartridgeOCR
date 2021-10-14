This is the code for the mobile Cartidge OCR Mobile app, which allows users to take pictures on their devices to add to the training set or to get a prediction on the image.

# Local Deployment
To get this running locally, run the following:
- `cd src/webapp/CartridgeOCRApp`
- `npm install -g @ionic/cli`
- `ionic build`
   - this might ask you to install react-scripts, respond yes if prompted
- `npm install -g serve`
- `serve -s build`

The app will be running locally at [http://localhost:5000]()