variable "resource_group_name" {
  type =  string
}

variable "storageaccountname"{
    type = string
}

variable "location"{
    type = string
}

variable "account_tier"{
    type = string
}

variable "account_replication_type"{
    type = string
}

variable "public_network_access_enabled" {
    type = bool
}

variable "account_kind" {
    type = string
}

variable "cross_tenant_replication_enabled" {
    type = bool
}

variable "access_tier" {
    type = string
}

variable "https_traffic_only_enabled" {
    type = bool
}

variable "min_tls_version" {
    type = string
}

variable "shared_access_key_enabled" {
    type = bool
}

variable "default_to_oauth_authentication" {
    type = bool
}

variable "is_hns_enabled" {
    type = bool
}

variable "nfsv3_enabled" {
    type = bool
}

variable "large_file_share_enabled" {
    type = bool
}

variable "local_user_enabled" {
    type = bool
}

variable "sftp_enabled" {
    type = bool
}

variable "allow_nested_items_to_be_public" {
    type = bool
}

variable "tags" {
    type = map(string) 
}
