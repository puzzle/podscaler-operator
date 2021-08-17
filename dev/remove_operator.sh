#/bin/bash
set -x
oc delete crd podscalers.puzzle.ch
oc delete serviceaccount podscaler-account
oc delete clusterrolebinding podscaler-rolebinding-cluster
oc delete rolebinding podscaler-rolebinding-namespaced
oc delete clusterrole podscaler-role-cluster
oc delete role podscaler-role-namespaced
