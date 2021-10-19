simra/reorg: based on ztoure/deploy
    - moved files so endpoint deployment doesn't scoop up the webapp.
    - AML/run_training.py needs to be tested
    - use this branch to redeploy the model endpoint
    - current issue is that CORS policy prohibits a call to the endpoint- call it from behind the upload API instead?

simra/deploywebapp: based on main
    - modifies the predict endpoint url specified in appConfig.json to point to the AKS endpoint
    - use this branch to redeploy the webapp

simra/hack21: come back to this branch and check for changes.