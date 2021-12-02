

## Deployment

Add more to the onboarding docs, especially for personal subsciption deployments.
Add AML endpoint configuration/setup scripts

deploy.sh is destructive and sometimes we just want to update something.
deploy.sh ensure it doesn't nuke training sets
deply.sh last deployment failed to assign service principal to gpucompute
learn more about terraform plans, management
Set up T4T azure subscription and migrate the deployments there

DONE: Create an NC6 GPU node instead of CPU cluster

## Labeler

new dataset.

Last hackathon Simon noted some additional EXIF tags we may want to capture. I'm not sure what the status is of those tags or where they were documented. 

We need a better workflow for organizing/staging incoming images and saving them for training.

DONE - All annotations in current set. Images have been uploaded for fresh annotation.
DONE - A new labeler was created but it has lots of images that were already labeled- separate the labeled from unlabeled images and create a 

## Training


Deploy model to FE prediction service.

Revive training_predictions for in-experiment and offline prediction. -- Predict.py has some good code for filtering spurious detections, and merging the casing and primer predictions to yield a more confident detection.

Cross-validation, hyperparameter optimization

render some outputs, look at the bad performers

Model selection - track best validation model

DONE - Model output folder should use experiment display name

DONE - Fix and post evaluation metrics - work in progress, see below.

DONE - There is a major bug in evaluate that prevents proper metrics evaluation.  In a nutshell the transforms are bypassed when the evaluator grabs the coco API from the dataset. We need the dataset to replace the coco instance with a corrected instance. This has been partially mitigated by "converting" the coco api at evaluation time. It's expensive because it requires re-opening every image and collecting its size- this should be fixed.  Also the mitigation only seems to work for the bounding boxes and not the polygons.

DONE - Bounding box vs segmentation evaluation
The evaluation metrics seem pretty poor but maybe this is expected. It may be worth validating on one or two images. We also need a lot more training data.

DONE - Add F1 metric to training progress.

## Webapp
ionic build a clean repo yields a lot of deprecation warnings:

- npm WARN deprecated babel-eslint@10.1.0: babel-eslint is now @babel/eslint-parser. This package will no longer receive updates.
- npm WARN deprecated querystring@0.2.1: The querystring API is considered Legacy. new code should use the URLSearchParams API instead.
- npm WARN deprecated sane@4.1.0: some dependency vulnerabilities fixed, support for node < 10 dropped, and newer ECMAScript syntax/features added
- npm WARN deprecated resolve-url@0.2.1: https://github.com/lydell/resolve-url#deprecated
- npm WARN deprecated urix@0.1.0: Please see https://github.com/lydell/urix#deprecated
- npm WARN deprecated flatten@1.0.3: flatten is deprecated in favor of utility frameworks such as lodash.
- npm WARN deprecated querystring@0.2.0: The querystring API is considered Legacy. new code should use the URLSearchParams API instead.
- npm WARN deprecated chokidar@2.1.8: Chokidar 2 will break on node v14+. Upgrade to chokidar 3 with 15x less dependencies.
- npm WARN deprecated fsevents@1.2.13: fsevents 1 will break on node v14+ and could be using insecure binaries. Upgrade to fsevents 2.
- npm WARN deprecated uuid@3.4.0: Please upgrade  to version 7 or higher.  Older versions may use Math.random() in certain circumstances, which is known to be problematic.  See https://v8.dev/blog/math-random for details.
- npm WARN deprecated rollup-plugin-babel@4.4.0: This package has been deprecated and is no longer maintained. Please use @rollup/plugin-babel.
- npm WARN deprecated @hapi/joi@15.1.1: Switch to 'npm install joi'
- npm WARN deprecated @hapi/topo@3.1.6: This version has been deprecated and is no longer supported or maintained
- npm WARN deprecated @hapi/bourne@1.3.2: This version has been deprecated and is no longer supported or maintained
- npm WARN deprecated @hapi/hoek@8.5.1: This version has been deprecated and is no longer supported or maintained
- npm WARN deprecated @hapi/address@2.1.4: Moved to 'npm install @sideway/address'
- npm WARN deprecated core-js@2.6.12: core-js@<3.3 is no longer maintained and not recommended for usage due to the number of issues. Because of the V8 engine whims, feature detection in old core-js versions could cause a slowdown up to 100x even if nothing is polyfilled. Please, upgrade your dependencies to the actual version of core-js.

Eventually we need the app to work in offline mode as well.

## Prediction endpoint

The only case that works E2E involves deploying the model and score file to kubernetes.  This is crazy expensive to host.
We can deploy the model to an azure container instance which is about $3-4/day.  
However to make this work from the webapp we have to deploy a TLS certificate and set up a DNS entry pointing at the host.  I haven't jumped through the steps to verify this is feasible. There were also some CORS issues but I think these are addressed in the current score.py script.

## Other prediction things

- make the predictions more robust by matching/pairing primer/casing detections.
- lots to do on the OCR side.

