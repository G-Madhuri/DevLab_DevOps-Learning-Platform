import os
import shutil
import pytest
from app.services.runtime import AzureShell, AzureRuntime
from app.services.validation import validation_engine

@pytest.fixture
def azure_shell():
    session_id = "test_azure_session"
    shell = AzureShell(session_id=session_id)
    yield shell
    if os.path.exists(shell.base_dir):
        shutil.rmtree(shell.base_dir, ignore_errors=True)

def test_azure_shell_whitelisted_commands(azure_shell):
    out = azure_shell.execute_command("pwd")
    assert "/" in out
    assert "student@devlab-azure:$" in out

    out_ver = azure_shell.execute_command("az --version")
    assert "azure-cli" in out_ver

    out_acc = azure_shell.execute_command("az account list")
    assert "DevLab Azure Subscription" in out_acc

def test_azure_shell_resource_groups(azure_shell):
    out_create = azure_shell.execute_command("az group create --name devlab-rg --location eastus")
    assert "devlab-rg" in out_create
    assert "devlab-rg" in azure_shell.azure_state["groups"]

    out_list = azure_shell.execute_command("az group list")
    assert "devlab-rg" in out_list

def test_azure_shell_virtual_machines(azure_shell):
    out_vm = azure_shell.execute_command("az vm create --resource-group devlab-rg --name devlab-vm --image Ubuntu2204")
    assert "devlab-vm" in out_vm
    assert "devlab-vm" in azure_shell.azure_state["vms"]

    out_list = azure_shell.execute_command("az vm list")
    assert "devlab-vm" in out_list

def test_azure_shell_networking_nsg(azure_shell):
    out_vnet = azure_shell.execute_command("az network vnet create --resource-group devlab-rg --name devlab-vnet --address-prefix 10.0.0.0/16")
    assert "devlab-vnet" in out_vnet
    assert "devlab-vnet" in azure_shell.azure_state["vnets"]

    out_subnet = azure_shell.execute_command("az network vnet subnet create --resource-group devlab-rg --vnet-name devlab-vnet --name devlab-subnet --address-prefix 10.0.1.0/24")
    assert "devlab-subnet" in out_subnet
    assert "devlab-subnet" in azure_shell.azure_state["subnets"]

    out_nsg = azure_shell.execute_command("az network nsg create --resource-group devlab-rg --name devlab-nsg")
    assert "devlab-nsg" in out_nsg
    assert "devlab-nsg" in azure_shell.azure_state["nsgs"]

    out_rule = azure_shell.execute_command("az network nsg rule create --resource-group devlab-rg --nsg-name devlab-nsg --name AllowHTTP --priority 100 --destination-port-ranges 80 --access Allow")
    assert "AllowHTTP" in out_rule
    assert "AllowHTTP" in azure_shell.azure_state["nsg_rules"]

def test_azure_shell_storage(azure_shell):
    out_acc = azure_shell.execute_command("az storage account create --name devlabstorage --resource-group devlab-rg --location eastus --sku Standard_LRS")
    assert "devlabstorage" in out_acc
    assert "devlabstorage" in azure_shell.azure_state["storage_accounts"]

    azure_shell.execute_command("echo 'test artifact' > test.txt")
    out_blob = azure_shell.execute_command("az storage blob upload --container-name artifacts --file test.txt --name test.txt")
    assert "test.txt" in out_blob
    assert "test.txt" in azure_shell.azure_state["blobs"]["artifacts"]

def test_azure_shell_sql(azure_shell):
    out_sql = azure_shell.execute_command("az sql server create --name devlab-sqlserver --resource-group devlab-rg --location eastus --admin-user sqladmin --admin-password Password123!")
    assert "devlab-sqlserver" in out_sql
    assert "devlab-sqlserver" in azure_shell.azure_state["sql_servers"]

    out_db = azure_shell.execute_command("az sql db create --resource-group devlab-rg --server devlab-sqlserver --name devlab-db")
    assert "devlab-db" in out_db
    assert "devlab-db" in azure_shell.azure_state["sql_dbs"]

def test_azure_shell_lb_vmss_monitor(azure_shell):
    out_lb = azure_shell.execute_command("az network lb create --resource-group devlab-rg --name devlab-lb --frontend-ip-name frontend")
    assert "devlab-lb" in out_lb
    assert "devlab-lb" in azure_shell.azure_state["load_balancers"]

    out_vmss = azure_shell.execute_command("az vmss create --resource-group devlab-rg --name devlab-vmss --image Ubuntu2204 --instance-count 2")
    assert "devlab-vmss" in out_vmss
    assert "devlab-vmss" in azure_shell.azure_state["vmss"]

    out_alert = azure_shell.execute_command("az monitor metrics alert create --name devlab-cpu-alert --resource-group devlab-rg")
    assert "devlab-cpu-alert" in out_alert
    assert "devlab-cpu-alert" in azure_shell.azure_state["alerts"]

def test_azure_validation_steps(azure_shell):
    azure_shell.execute_command("az --version")
    res1 = validation_engine._validate_azure(azure_shell, 1, "azure-fundamentals")
    assert res1["success"] is True

    azure_shell.execute_command("pwd")
    res2 = validation_engine._validate_azure(azure_shell, 2, "azure-fundamentals")
    assert res2["success"] is True

    azure_shell.execute_command("ls")
    res3 = validation_engine._validate_azure(azure_shell, 3, "azure-fundamentals")
    assert res3["success"] is True

    azure_shell.execute_command("cat main.tf")
    res4 = validation_engine._validate_azure(azure_shell, 4, "azure-fundamentals")
    assert res4["success"] is True

    azure_shell.execute_command("az group list")
    res5 = validation_engine._validate_azure(azure_shell, 5, "azure-fundamentals")
    assert res5["success"] is True

    azure_shell.execute_command("az vm list")
    res6 = validation_engine._validate_azure(azure_shell, 6, "azure-fundamentals")
    assert res6["success"] is True

    azure_shell.execute_command("az storage account list")
    res7 = validation_engine._validate_azure(azure_shell, 7, "azure-fundamentals")
    assert res7["success"] is True

    azure_shell.execute_command("az account list")
    res8 = validation_engine._validate_azure(azure_shell, 8, "azure-fundamentals")
    assert res8["success"] is True

def test_azure_capstone_validation(azure_shell):
    azure_shell.execute_command("terraform apply")
    azure_shell.execute_command("curl http://127.0.0.1/health")
    res = validation_engine._validate_azure(azure_shell, 8, "azure-capstone-project")
    assert res["success"] is True
