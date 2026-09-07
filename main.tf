 provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "acr" {
  name     = "acr-cortex-sandbox-rg"
  location = "Canada Central"
}

resource "azurerm_container_registry" "acr_pass" {
  name                          = "acrcortexpass01"
  resource_group_name           = azurerm_resource_group.acr.name
  location                      = azurerm_resource_group.acr.location
  sku                           = "Premium"
  admin_enabled                 = false
  anonymous_pull_enabled        = false
  public_network_access_enabled = false
}

resource "azurerm_container_registry" "acr_fail" {
  name                          = "acrcortexfail01"
  resource_group_name           = azurerm_resource_group.acr.name
  location                      = azurerm_resource_group.acr.location
  sku                           = "Basic"
  admin_enabled                 = true
  public_network_access_enabled = true
}
