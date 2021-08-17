# Podscaler-Operator
Down and upscale of your pods with a CustomResource in a target-namespace while storing the replica count. This helps when a large number of namespaces have to be scaled for maintenance work and the same state is to be restored later.

## Supported platforms
Tested on OpenShift 4.8.x

TODO: "Add support for all api-versions since 1.11"
To get it running on older versions of OpenShift change the api versions in the function: set_resource_type.

### Supported resources
- "DeploymentConfig": "apps.openshift.io/v1"
- "Deployment": "apps/v1"
- "StatefulSet": "apps/v1"
- "DaemonSet": "apps/v1" (Optional)

## Deployment
```bash
# create a namespace
oc new-project podscaler-operator

## deploy operator (default-namespace: podscaler-operator)
oc process -f deployment.yaml | oc create -f -
```

## Usage
1. Make sure the operator is deployed and has the required permissions
2. Now create a CustomResource for your target namespace
```
---
# example object
apiVersion: puzzle.ch/v1
kind: PodScaler
metadata:
  name: pitc-namespace-test
spec:
  namespace: pitc-namespace-test
  status: down
  filter: ""
  no_daemonset: false
```
3. At this point: The Operator can affect the resources in the target namespace

## Access-Matrix
TODO: Fix permissions (currently cluster-admin role used for the Operator)

## Development
Current BaseImage: Ubuntu:20.04
Python-Version: 3.8.x
