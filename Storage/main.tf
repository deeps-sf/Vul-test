resource "azurerm_storage_account" "azurestor1" {
  name                             = var.storageaccountname
  resource_group_name              = var.resource_group_name
  location                         = var.location
  account_tier                     = var.account_tier
  account_replication_type         = var.account_replication_type
  public_network_access_enabled    = var.public_network_access_enabled
  account_kind                     = var.account_kind
  cross_tenant_replication_enabled = var.cross_tenant_replication_enabled
  access_tier                      = var.access_tier
  min_tls_version                  = var.min_tls_version
  shared_access_key_enabled        = var.shared_access_key_enabled
  default_to_oauth_authentication  = var.default_to_oauth_authentication
  is_hns_enabled                   = var.is_hns_enabled
  nfsv3_enabled                    = var.nfsv3_enabled
  large_file_share_enabled         = var.large_file_share_enabled
  local_user_enabled               = var.local_user_enabled
  sftp_enabled                     = var.sftp_enabled
  https_traffic_only_enabled       = var.https_traffic_only_enabled
  allow_nested_items_to_be_public  = var.allow_nested_items_to_be_public
  tags = merge(var.tags, {
    Vul       = ""
    abcde     = ""
    manny     = "cepeda"
    test2     = "test2"
    yor_trace = "e5d85ddf-e994-43a5-9f14-2a5fc3a4818b"
  })
}
