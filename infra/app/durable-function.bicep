param name string
param location string = resourceGroup().location
param tags object = {}
param applicationInsightsName string = ''
param appServicePlanId string
param appSettings object = {}
param runtimeName string 
param runtimeVersion string 
param serviceName string = 'function-app'
param storageAccountName string
param virtualNetworkSubnetId string = ''
param identityId string = ''
param identityClientId string = ''
param dtmbURL string = ''
param taskHubName string = ''
param azureOpenaiService string
param azureOpenaiChatgptDeployment string
param documentIntelligenceEndpoint string

var applicationInsightsIdentity = 'ClientId=${identityClientId};Authorization=AAD'


module durableFunction '../core/host/functions.bicep' = {
  name: '${serviceName}-functions-module'
  params: {
    name: name
    location: location
    tags: union(tags, { 'azd-service-name': serviceName })
    identityType: 'UserAssigned'
    identityId: identityId
    appSettings: union(appSettings,
      {
        AzureWebJobsStorage__clientId : identityClientId
        AzureWebJobsStorage__credential : 'managedidentity'
        APPLICATIONINSIGHTS_AUTHENTICATION_STRING: applicationInsightsIdentity
        AZURE_CLIENT_ID: identityClientId
      })
    documentIntelligenceEndpoint: documentIntelligenceEndpoint
    azureOpenaiService: azureOpenaiService
    azureOpenaiChatgptDeployment: azureOpenaiChatgptDeployment
    applicationInsightsName: applicationInsightsName
    appServicePlanId: appServicePlanId
    runtimeName: runtimeName
    runtimeVersion: runtimeVersion
    storageAccountName: storageAccountName
    storageManagedIdentity: true
    virtualNetworkSubnetId: virtualNetworkSubnetId
  }
}

output SERVICE_DURABLE_FUNCTION_NAME string = durableFunction.outputs.name
output SERVICE_API_IDENTITY_PRINCIPAL_ID string = durableFunction.outputs.identityPrincipalId
