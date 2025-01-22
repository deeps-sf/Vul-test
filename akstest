provider "azurerm" {
  features {}
}

data "azuread_client_config" "current" {}
data "azurerm_client_config" "current" {}

locals {
  akscluster01 = {
    kubernetes_version = "1.30.4"
    logws              = "law-${var.medline_default_location}-${var.environment}-workspace01"
    aks_tags = {
      "Application Name"    = "AKS Infrastructure"
      "Team Name"           = "Cloud Product Team"
      "Cost Center"         = "97100"
      "IS Owner"            = "John Mckeown"
      "Business Unit Owner" = "Eric Odell"
      "Created By"          = "master-az"
      "Environment"         = "sbx"
      "Requested By"        = "Cloud Product Team"
      "Medline Tier"        = "Tier 3"
      "STAR"                = ""
      "POC Expiration"      = ""
      "PHI Data"            = "No"
    }
    default_node_pool = {
      name                 = "agentpool02"
      vm_size              = "Standard_DS3_v2"
      os_disk_size_gb      = 30
      type                 = "VirtualMachineScaleSets"
      orchestrator_version = "1.30.4"
      max_pods             = 50
      enable_auto_scaling  = true
      min_count            = 3
      max_count            = 4
      availability_zones   = ["1", "2", "3"]
    }
    teams = {
      medpack = {
        namespace         = "manufacturingapps-medpack-${var.environment}"
        kube_admin        = "ML-Azure-Kube-Medpack-Admin"
        kube_read         = "ML-Azure-Kube-Medpack-Read"
        tf_workspace_name = "az-spoke-manufacturingapps-medpack-infra-${var.environment}"
        cpu               = "16"
        memory            = "40Gi"
      }
      smartquote = {
        namespace         = "pricing-smartquote-${var.environment}"
        kube_admin        = "ML-Azure-Kube-Pricing-Admin"
        kube_read         = "ML-Azure-Kube-Pricing-Read"
        tf_workspace_name = "az-spoke-pricing-smartquote-infra-${var.environment}"
        cpu               = "32"
        memory            = "85Gi"
      }
      ecom = {
        namespace         = "ecom-customernotifications-${var.environment}"
        kube_admin        = "ML-Azure-Kube-ECOM-Operations-SBX"
        kube_read         = "ML-Azure-Kube-ECOM-Developers-SBX"
        tf_workspace_name = "az-spoke-manufacturingapps-medpack-infra-${var.environment}"
        cpu               = "16"
        memory            = "40Gi"
      }
      enterpriseanalytics = {
        namespace         = "enterpriseanalytics-descriptionanalyzer-${var.environment}"
        kube_admin        = "ML-Azure-DevOps"
        kube_read         = "ML-Azure-Kube-MachineLearning-Developers-SBX"
        tf_workspace_name = "az-spoke-enterpriseanalytics-descriptionanalyzer-infra-${var.environment}"
        cpu               = "16"
        memory            = "40Gi"
      }
    }
  }
}

data "azurerm_subnet" "aks_subnet" {
  name                 = var.azure_aks_subnet_name
  resource_group_name  = var.vnet_resource_group
  virtual_network_name = var.vnet_name
}

data "azurerm_resource_group" "aks_rg" {
  name = var.azure_resource_group_name
}

data "azurerm_log_analytics_workspace" "aks_logws" {

  name                = local.akscluster01.logws
  resource_group_name = var.azure_monitor_resource_group_name
}

data "azuread_group" "kube_admin" {
  for_each = local.akscluster01.teams

  display_name = each.value.kube_admin
}

data "azuread_group" "aad_admin" {
  display_name = "ML-Azure-Kube-Admin-${upper(var.environment)}"
}

data "azuread_group" "kube_reader" {

  display_name = "ML-Azure-Kube-Reader-${upper(var.environment)}"
}
resource "azurerm_role_assignment" "aks_rg_reader_kube_admin" {
  for_each = local.akscluster01.teams

  scope                = data.azurerm_resource_group.aks_rg.id
  role_definition_name = "Reader"
  principal_id         = data.azuread_group.kube_admin[each.key].id
}

resource "azurerm_role_assignment" "aks_user_role_admin" {
  for_each = local.akscluster01.teams

  scope                = azurerm_kubernetes_cluster.aks_cluster.id
  role_definition_name = "Azure Kubernetes Service Cluster User Role"
  principal_id         = data.azuread_group.kube_admin[each.key].id
}

data "azuread_group" "kube_read" {
  for_each = local.akscluster01.teams

  display_name = each.value.kube_read
}

resource "azurerm_role_assignment" "aks_rg_reader_kube_read" {
  for_each = local.akscluster01.teams

  scope                = data.azurerm_resource_group.aks_rg.id
  role_definition_name = "Reader"
  principal_id         = data.azuread_group.kube_read[each.key].id
}

data "azurerm_key_vault_secret" "kubecost_token" {
  name         = "kubecosttoken"
  key_vault_id = azurerm_key_vault.aks_kv.id
}

resource "azurerm_role_assignment" "aks_user_role_read" {
  for_each = local.akscluster01.teams

  scope                = azurerm_kubernetes_cluster.aks_cluster.id
  role_definition_name = "Azure Kubernetes Service Cluster User Role"
  principal_id         = data.azuread_group.kube_read[each.key].id
}

resource "azurerm_kubernetes_cluster" "aks_cluster" {
  # checkov:skip=CKV_AZURE_7: AKS cluster network policies are not enforced - LOW
  # checkov:skip=CKV_AZURE_8: Kubernetes dashboard is not disabled - LOW
  # checkov:skip=CKV_AZURE_115: AKS is not enabled for private clusters - LOW
  # checkov:skip=CKV_AZURE_117: AKS does not use disk encryption set - LOW
  # checkov:skip=CKV_AZURE_141: AKS local admin account is disabled - LOW

  name                = "aks-${var.medline_default_location}-${var.environment}-akscluster01"
  location            = data.azurerm_resource_group.aks_rg.location
  dns_prefix          = "aks-${var.medline_default_location}-${var.environment}-akscluster01"
  resource_group_name = data.azurerm_resource_group.aks_rg.name
  kubernetes_version  = local.akscluster01.kubernetes_version
  cost_analysis_enabled = true
  #api_server_authorized_ip_ranges  = ["205.233.244.5/32", "205.233.246.4/32", "205.233.247.4/32", "13.86.36.39/32", "50.223.46.210/32", "13.86.59.83/32", "13.86.60.97/32", "103.127.255.4/32", "20.84.170.124/32"]
  http_application_routing_enabled = false
  node_os_channel_upgrade          = "SecurityPatch"
  api_server_access_profile {
    authorized_ip_ranges = ["205.233.244.5/32", "205.233.246.4/32", "205.233.247.4/32", "13.86.36.39/32", "50.223.46.210/32", "13.86.59.83/32", "13.86.60.97/32", "103.127.255.4/32", "20.84.170.124/32", "172.174.255.114/31", "172.178.96.56/31", "20.55.71.224/31"]
  }
  maintenance_window_node_os {
    frequency   = "Weekly"
    interval    = "1"
    day_of_week = "Monday"
    utc_offset  = "+05:30"
    start_time  = "18:30"
    duration    = "5"
  }

  default_node_pool {
    name                = local.akscluster01.default_node_pool.name
    vm_size             = local.akscluster01.default_node_pool.vm_size
    os_disk_size_gb     = local.akscluster01.default_node_pool.os_disk_size_gb
    type                = local.akscluster01.default_node_pool.type
    max_pods            = local.akscluster01.default_node_pool.max_pods
    enable_auto_scaling = local.akscluster01.default_node_pool.enable_auto_scaling
    #node_count           = 3
    min_count                    = local.akscluster01.default_node_pool.min_count
    max_count                    = local.akscluster01.default_node_pool.max_count
    orchestrator_version         = local.akscluster01.default_node_pool.orchestrator_version
    enable_host_encryption       = true
    only_critical_addons_enabled = true
    #availability_zones   = local.akscluster01.default_node_pool.availability_zones
    zones = local.akscluster01.default_node_pool.availability_zones
    # Required for advanced networking
    vnet_subnet_id = data.azurerm_subnet.aks_subnet.id
    tags           = local.akscluster01.aks_tags
    #temporary_name_for_rotation = "tmppool01"
    //upgrade_settings {
    //max_surge = 2
    ## or max_surge = 50%
    //}
  }

  /*service_principal {
    client_id     = var.client_id
    client_secret = var.client_secret
  }*/

  storage_profile {
    disk_driver_enabled         = true
    file_driver_enabled         = false
    snapshot_controller_enabled = false
  }

  auto_scaler_profile {

    balance_similar_node_groups = true

  }

  identity {
    type = "SystemAssigned" 
  }

  azure_active_directory_role_based_access_control {
    managed                = true
    azure_rbac_enabled     = true
    admin_group_object_ids = [data.azuread_group.aad_admin.id]

    /*azure_active_directory {
      managed                = true
      admin_group_object_ids = [data.azuread_group.aad_admin.id]
    } */
  }

  azure_policy_enabled = true

  /*    http_application_routing {
      enabled = false

    }

    kube_dashboard {
      enabled = true
    } */
  oms_agent {
    #enabled                    = true
    log_analytics_workspace_id = replace(replace(data.azurerm_log_analytics_workspace.aks_logws.id, "microsoft.operationalinsights", "Microsoft.OperationalInsights"), "resourcegroups", "resourceGroups")
  }

  microsoft_defender {
    log_analytics_workspace_id = data.azurerm_log_analytics_workspace.loganalyticsws.id
  }


  network_profile {
    dns_service_ip     = "172.28.224.10"
    load_balancer_sku  = "standard"
    docker_bridge_cidr = "172.28.240.1/20"
    network_plugin     = "azure"
    service_cidr       = "172.28.224.0/20"
  }

  tags     = local.akscluster01.aks_tags
  sku_tier = "Standard"

  lifecycle {
    ignore_changes = [
      windows_profile, default_node_pool[0].node_count
    ]
  }
}

resource "azurerm_kubernetes_cluster_node_pool" "usernodepool02" {
  kubernetes_cluster_id  = azurerm_kubernetes_cluster.aks_cluster.id
  name                   = "userpool02"
  vm_size                = "Standard_DS3_v2"
  os_disk_size_gb        = 30
  max_pods               = 30
  enable_auto_scaling    = true
  min_count              = 3
  max_count              = 4
  orchestrator_version   = "1.30.4"
  enable_host_encryption = true
  zones                  = ["1", "2", "3"]
  # Required for advanced networking
  vnet_subnet_id = data.azurerm_subnet.aks_subnet.id
  tags           = local.akscluster01.aks_tags
  mode           = "User"
  upgrade_settings {
    max_surge = 2
    ## or max_surge = 50% 
  }
}

data "azurerm_log_analytics_workspace" "loganalyticsws" {
  name                = "law-usce-sbx-001"
  resource_group_name = "rg-sbx-securityservices"
}

data "azurerm_resource_group" "aks_mc_rg" {
  name = azurerm_kubernetes_cluster.aks_cluster.node_resource_group

}

data "azurerm_resources" "aks-cluster-lb" {
  resource_group_name = data.azurerm_resource_group.aks_mc_rg.name
  type                = "Microsoft.Network/loadBalancers"

}

module "diagnostic_settings_aks_lb" {
  #source = "git::ssh://git@bitbucket.org/medlineis/terraform-modules.git//azure/resources/terraform-azure-diagnostic-setting"
source  = "app.terraform.io/medline/diagnostic-setting-module/azure"
version = "1.0.0"
  count                      = length(data.azurerm_resources.aks-cluster-lb.resources)
  name                       = "diag-setting-${data.azurerm_resources.aks-cluster-lb.resources[count.index].name}"
  resource_id                = data.azurerm_resources.aks-cluster-lb.resources[count.index].id
  log_analytics_workspace_id = data.azurerm_log_analytics_workspace.loganalyticsws.id
  retention_days             = 90

}



module "diagnostic_settings_aks_cluster01" {
  source                     = "git::ssh://git@bitbucket.org/medlineis/terraform-modules.git//azure/resources/terraform-azure-diagnostic-setting"
  name                       = "diag-setting-akscluster01"
  resource_id                = azurerm_kubernetes_cluster.aks_cluster.id
  log_analytics_workspace_id = data.azurerm_log_analytics_workspace.loganalyticsws.id
  retention_days             = 90
}

resource "azurerm_key_vault" "aks_kv" {
  name                = "vault-${var.environment}-akscluster"
  resource_group_name = data.azurerm_resource_group.aks_rg.name
  location            = data.azurerm_resource_group.aks_rg.location
  sku_name            = "standard"
  tenant_id           = data.azuread_client_config.current.tenant_id

  enabled_for_disk_encryption     = true
  enabled_for_deployment          = true
  enabled_for_template_deployment = true
  purge_protection_enabled        = true
  network_acls {
    default_action             = "Deny"
    bypass                     = "AzureServices"
    ip_rules                   = ["205.233.244.5", "205.233.246.4", "205.233.247.4", "50.223.46.210", "103.127.255.7"]
    virtual_network_subnet_ids = ["/subscriptions/2b87dee0-a31b-419f-94ab-192627b1321d/resourceGroups/rg-sbx-networkservices/providers/Microsoft.Network/virtualNetworks/vnet-usce-sbx-spoke-vnetid903/subnets/snet-usce-sbx-vnetid903-aksclustersvc", "/subscriptions/84740e5e-19b4-4fd2-a5d4-45937be5c7e8/resourceGroups/rg-tst-networkservices/providers/Microsoft.Network/virtualNetworks/vnet-usce-tst-spoke-vnetid200/subnets/snet-usce-tst-vnetid200-aksclustersvc"]
  }

  tags = local.akscluster01.aks_tags
}


resource "azurerm_private_endpoint" "keyvault_privendpoint" {
  name                = "privlink-${azurerm_key_vault.aks_kv.name}"
  location            = "Central US"
  resource_group_name = "rg-sbx-networkservices"
  subnet_id           = data.azurerm_subnet.endpoints.id
  tags                = local.akscluster01.aks_tags

  private_service_connection {
    name                           = "privsvc-${azurerm_key_vault.aks_kv.name}"
    private_connection_resource_id = azurerm_key_vault.aks_kv.id
    is_manual_connection           = true
    request_message                = "approve"
    subresource_names              = ["vault"]
  }
}

data "azurerm_subnet" "endpoints" {
  name                 = "snet-usce-sbx-vnetid903-privatelinksvc"
  virtual_network_name = "vnet-usce-sbx-spoke-vnetid903"
  resource_group_name  = "rg-sbx-networkservices"
}

module "diagnostic_settings_key_vault" {
  source = "git::ssh://git@bitbucket.org/medlineis/terraform-modules.git//azure/resources/terraform-azure-diagnostic-setting"

  name               = "diag-setting-keyvault"
  resource_id        = azurerm_key_vault.aks_kv.id
  storage_account_id = azurerm_storage_account.aks_storage.id
  retention_days     = 90
}

module "diagnostic_settings_key_vault01" {
  source = "git::ssh://git@bitbucket.org/medlineis/terraform-modules.git//azure/resources/terraform-azure-diagnostic-setting"

  name                       = "diag-setting-keyvault01"
  resource_id                = azurerm_key_vault.aks_kv.id
  log_analytics_workspace_id = data.azurerm_log_analytics_workspace.loganalyticsws.id
  retention_days             = 90
}

resource "azurerm_key_vault_access_policy" "aks_SP" {
  key_vault_id            = azurerm_key_vault.aks_kv.id
  tenant_id               = data.azuread_client_config.current.tenant_id
  object_id               = data.azuread_client_config.current.object_id
  key_permissions         = ["Get", "List", "Update", "Create", "Delete"]
  secret_permissions      = ["Get", "List", "Set", "Delete"]
  certificate_permissions = ["Get", "List", "Create", "Update", "Delete"]
}

/*resource "azurerm_management_lock" "kubernetes_cluster" {
  name       = "resourcecluster"
  scope      = azurerm_kubernetes_cluster.aks_cluster.id
  lock_level = "CanNotDelete"
  notes      = "Locked to prevent deletion by accident"
} */


/*--------------------------Storage Account for Logs --------------------*/
resource "azurerm_storage_account" "aks_storage" {
  # checkov:skip=CKV_AZURE_59: Storage accounts disallow public access - LOW
  name                            = "stor${var.medline_default_location}${var.environment}akslogs"
  resource_group_name             = data.azurerm_resource_group.aks_rg.name
  location                        = data.azurerm_resource_group.aks_rg.location
  account_kind                    = "BlobStorage"
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  enable_https_traffic_only       = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  identity {
    type = "SystemAssigned"
  }

  network_rules {
    default_action             = "Deny"
    bypass                     = ["AzureServices"]
    ip_rules                   = ["205.233.244.5", "205.233.246.4", "205.233.247.4", "50.223.46.210", "103.127.255.7"]
    virtual_network_subnet_ids = ["/subscriptions/2b87dee0-a31b-419f-94ab-192627b1321d/resourceGroups/rg-sbx-networkservices/providers/Microsoft.Network/virtualNetworks/vnet-usce-sbx-spoke-vnetid903/subnets/snet-usce-sbx-vnetid903-aksclustersvc", "/subscriptions/2b87dee0-a31b-419f-94ab-192627b1321d/resourceGroups/rg-sbx-networkservices/providers/Microsoft.Network/virtualNetworks/vnet-usce-sbx-spoke-vnetid903/subnets/snet-usce-sbx-vnetid903-networksvc", "/subscriptions/2b87dee0-a31b-419f-94ab-192627b1321d/resourceGroups/rg-sbx-networkservices/providers/Microsoft.Network/virtualNetworks/vnet-usce-sbx-spoke-vnetid903/subnets/snet-usce-sbx-vnetid903-privatelinksvc", "/subscriptions/2b87dee0-a31b-419f-94ab-192627b1321d/resourceGroups/rg-sbx-networkservices/providers/Microsoft.Network/virtualNetworks/vnet-usce-sbx-spoke-vnetid903/subnets/snet-usce-sbx-vnetid903-securitysvc"]
  }

  tags = local.akscluster01.aks_tags

  lifecycle {
    ignore_changes = [
      customer_managed_key
    ]
  }

}

data "azurerm_key_vault" "key_vault" {
  name                = "vault-sbx-storage"
  resource_group_name = "rg-sbx-securityservices"
}

resource "azurerm_key_vault_access_policy" "aks_storage_sbx_policy" {
  key_vault_id = data.azurerm_key_vault.key_vault.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_storage_account.aks_storage.identity.0.principal_id

  key_permissions    = ["Get", "Create", "List", "Delete", "Restore", "Recover", "UnwrapKey", "WrapKey", "Purge", "Encrypt", "Decrypt", "Sign", "Verify"]
  secret_permissions = ["Get"]
}

resource "azurerm_key_vault_key" "aks_storage_sbx_key" {
  # checkov:skip=CKV_AZURE_112: Key vault key is not backed by HSM - LOW
  name            = "CMK-storuscesbxakslogs"
  key_vault_id    = data.azurerm_key_vault.key_vault.id
  key_type        = "RSA"
  key_size        = 2048
  key_opts        = ["decrypt", "encrypt", "sign", "unwrapKey", "verify", "wrapKey"]
  expiration_date = "2024-12-31T20:00:00Z"

  depends_on = [
    azurerm_key_vault_access_policy.aks_storage_sbx_policy
  ]
}

resource "azurerm_storage_account_customer_managed_key" "aks_storage_sbx_key" {
  storage_account_id = azurerm_storage_account.aks_storage.id
  key_vault_id       = data.azurerm_key_vault.key_vault.id
  key_name           = "CMK-storuscesbxakslogs"
}
