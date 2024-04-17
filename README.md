# Assignment 3 - AI Photo Service - NYU Cloud Computing 

The `client` folder contains the frontend, which is hosted on a public S3 bucket. It also contains the `buildspec.yml` file used in the build step of the FrontendPipeline(P2). 

This pipeline is triggered on every code commit, and simply copies the code inside client to the bucket.

The `lambdas` folder contains the backend code. There are 2 folders inside, which contain the code for `search-photos` and `index-photos`. It has `requirements.txt`, the common requirements for both the functions.  It also contains the `buildspec.yml` file used in the build step of the LambdaPipeline(P1). 

The `build` step install dependencies to a temp folder, and copies these folders into the folders of the functions, and then creates a zip file of each folder. The `post-build` step directly updates the function code for the functions through the AWS CLI, which effectively deploys the function, by sending appropriate zip files. These zip files are also build artifacts, which are then stored in an S3 bucket in the "Store" stage, to be used by CloudFormation template.
This pipeline is also triggered on ever code commit.

`apigateway.yaml` has the OpenAPI spec of the deployed API Gateway, with all the necessary settings to make `x-amz-meta-customlabels` custom header work with PUT requests, as well as all necessary steps for enabling CORS. 

`cf.yaml` contains the template for a stack deployment of CloudFormation for this project. It creates 2 Lambda Functions, an API Gateway, and 2 S3 buckets to store photos and serve the frontend. It also creates all the necessary roles and permissions required for the app to function.

