#!/usr/bin/python
"""
Operator to scale a namespace up and down while holding the replica state
within the target resources.
"""

from openshift.dynamic import DynamicClient
from kubernetes import client, config
import kopf


def get_res_obj(dyn_client, namespace, kind, api_version):
    """ This function gets a specific resource type from a namespace
    Args:
        dyn_client (openshift.dynamic.client.DynamicClient)
        namespace (str)
        kind (str)
        api_version (str)
    Returns:
        openshift.dynamic.resource.ResourceInstance
    """
    v1_deployment = dyn_client.resources.get(
        api_version=api_version,
        kind=kind
    )
    return v1_deployment.get(namespace=namespace)


def get_all_res_obj(dyn_client, namespace, resource_dict):
    """Return list object for requested resources
    Args:
        dyn_client (openshift.dynamic.client.DynamicClient)
        namespace (str)
        resource_dict (dict)
    Returns:
        list
    """
    obj_list = []
    for key, value in resource_dict.items():
        obj_list.append(get_res_obj(dyn_client, namespace, key, value))
    return obj_list


def scale_up_daemonset(res):
    """returns scale_down body for DaemonSet
    Args:
        res (dict)
    Returns:
        dict
    """
    body = {
        'kind': res['kind'],
        'apiVersion': res['apiVersion'],
        'metadata': {
            'name': res['name'],
        },
        'spec': {
            'template': {
                'spec': {
                    'nodeSelector': {
                        "pod_scaler_daemonset_selector": None
                    }
                }
            }
        }
    }
    return body


def scale_up_default(res):
    """returns scale_up body for
    DeploymentConfig, Deployment and StatefulSet
    Args:
        res (dict)
    Returns:
        dict
    """
    body = {
        'kind': res['kind'],
        'apiVersion': res['apiVersion'],
        'metadata': {'name': res['name']},
        'spec': {
            'replicas': int(res['replica_state'])
        }
    }
    return body


def scale_down_default(res):
    """returns scale_down body for
    DeploymentConfig, Deployment and StatefulSet
    Args:
        res (dict)
    Return:
        dict
    """
    body = {
        'kind': res['kind'],
        'apiVersion': res['apiVersion'],
        'metadata': {
            'name': res['name'],
            'annotations': {
                'pod_scaler_replication_state': str(res['replicas'])
            }
        },
        'spec': {
            'replicas': 0
        }
    }
    return body


def scale_down_daemonset(res):
    """returns scale_down body for DaemonSet
    Args:
       res (dict)
    Returns:
       dict
    """
    body = {
        'kind': res['kind'],
        'apiVersion': res['apiVersion'],
        'metadata': {
            'name': res['name'],
        },
        'spec': {
            'template': {
                'spec': {
                    'nodeSelector': {
                        "pod_scaler_daemonset_selector": "true"
                    }
                }
            }
        }
    }
    return body


def filter_all_obj(obj_list):
    """returns list of specific required resources
    attributes from currently existing resources
    Args:
         obj_list (list)
    Returns:
         list
    """
    meta_resource_list = []
    for obj in obj_list:
        for res in obj.items:
            meta_resource = {}
            meta_resource['name'] = res.metadata.name
            meta_resource['kind'] = res.kind
            meta_resource['apiVersion'] = res.apiVersion
            try:
                meta_resource['labels'] = res.metadata.labels
            except AttributeError:
                meta_resource['labels'] = "None"
            try:
                meta_resource['replicas'] = res.spec.replicas
            except AttributeError:
                meta_resource['replicas'] = "None"
            try:
                meta_resource['replica_state'] = res.metadata.annotations.pod_scaler_replication_state
            except AttributeError:
                meta_resource['replica_state'] = 0
            meta_resource_list.append(meta_resource)
    return meta_resource_list


def dyn_client_auth():
    """ensure the api authentication
    for the dynamic-client, piggibacked
    on kopf"""
    config.load_incluster_config()
    k8s_config = client.Configuration()
    k8s_client = client.api_client.ApiClient(configuration=k8s_config)
    return DynamicClient(k8s_client)


def set_resource_type(no_daemonset):
    """Include or exclude daemonset resource from
    used set of resources"""
    if no_daemonset:
        resource_dict = {
            "DeploymentConfig": "apps.openshift.io/v1",
            "Deployment": "apps/v1",
            "StatefulSet": "apps/v1",
        }
    else:
        resource_dict = {
            "DeploymentConfig": "apps.openshift.io/v1",
            "Deployment": "apps/v1",
            "StatefulSet": "apps/v1",
            "DaemonSet": "apps/v1"
        }
    return resource_dict


def scale(dyn_client, namespace, res):
    """scales resources in target namespace
    using the k8s-api
    Args:
        dyn_client (openshift.dynamic.client.DynamicClient)
        namespace(str)
        res(dict)
    Returns:
        None
    """
    if res['scale'] == 'down':
        if res['kind'] == 'DaemonSet':
            body = scale_down_daemonset(res)
        else:
            body = scale_down_default(res)
    else:
        if res['kind'] == 'DaemonSet':
            body = scale_up_daemonset(res)
        else:
            body = scale_up_default(res)

    v1_deployment = dyn_client.resources.get(
        api_version=res['apiVersion'],
        kind=res['kind']
    )
    try:
        v1_deployment.patch(body=body, namespace=namespace)
    except Exception as err:
        print("scale of resource: {0} "
              "failed with error: {1}".format(res['name'], err))


def main_scale(namespace_resources, namespace, dyn_client, status):
    """ main function to choose scale case """
    for item in namespace_resources:
        # scale down
        if status == "down":
            if item['kind'] == "DaemonSet":
                item.update(scale='down')
                scale(dyn_client, namespace, item)
            else:
                if item['replicas'] == 0:
                    print("nothing to scale up, {0} has "
                          "already replication_state: "
                          "{1}".format(item['name'], item['replica_state']))
                else:
                    item.update(scale='down')
                    scale(dyn_client, namespace, item)
        # scale up
        if status == "up":
            if item['kind'] == "DaemonSet":
                item.update(scale='up')
                scale(dyn_client, namespace, item)
            else:
                if int(item['replica_state']) == int(item['replicas']):
                    print("nothing to scale up, {0} has "
                          "already replication_state: "
                          "{1}".format(item['name'], item['replica_state']))
                else:
                    item.update(scale='up')
                    scale(dyn_client, namespace, item)


def requirement_error_check(namespace, status):
    """error check function"""
    if not namespace:
        raise kopf.PermanentError(f"Namespace must be set. Got {namespace!r}.")
    if not status:
        raise kopf.PermanentError(f"Status must be set. Got {status!r}.")


@kopf.on.create('puzzle.ch', 'v1', 'podscalers')
def create_fn(spec, **kwargs):
    """ resource create handler """

    # gather data from resource-spec
    namespace = spec.get('namespace')
    status = spec.get('status')
    #filter = spec.get('filter')
    no_daemonset = spec.get('no_daemonset')
    requirement_error_check(namespace, status)

    # authenticate against the cluster
    dyn_client = dyn_client_auth()

    # set requested resource kinds
    resource_dict = set_resource_type(no_daemonset)

    # gather information from cluster
    namespace_resources = filter_all_obj(
        get_all_res_obj(dyn_client, namespace, resource_dict)
    )
    # scale the traget namspace
    main_scale(namespace_resources, namespace, dyn_client, status)


@kopf.on.update('puzzle.ch', 'v1', 'podscalers')
def update_fn(spec, **kwargs):
    """ resource update handler """

    # re-check specs in definition
    namespace = spec.get('namespace')
    status = spec.get('status')
    #filter = spec.get('filter')
    no_daemonset = spec.get('no_daemonset')
    requirement_error_check(namespace, status)

    # authenticate against the cluster
    dyn_client = dyn_client_auth()

    # set requested resource_kinds
    resource_dict = set_resource_type(no_daemonset)

    # gather information from cluster
    namespace_resources = filter_all_obj(
        get_all_res_obj(dyn_client, namespace, resource_dict)
    )
    # scale the traget namspace
    main_scale(namespace_resources, namespace, dyn_client, status)
