import pulumi
from pulumi_yandex import compute_instance, Provider

# Данные для подключения к Yandex Cloud (явно в коде)
YC_TOKEN = ""
YC_CLOUD_ID = ""
YC_FOLDER_ID = ""
YC_ZONE = ""

# Получаем SSH ключ из конфигурации Pulumi
config = pulumi.Config()
ssh_public_key = config.require_secret("ssh_public_key")

# Данные из Terraform VM
subnet_id = ""
image_id = ""

# Создаем провайдера с УНИКАЛЬНЫМ именем (не 'yandex')
yandex_provider = Provider("yandex-cloud-provider",  # Уникальное имя!
    token=YC_TOKEN,
    cloud_id=YC_CLOUD_ID,
    folder_id=YC_FOLDER_ID,
    zone=YC_ZONE
)

# Создаем ВМ
vm = compute_instance.ComputeInstance("lab4-vm",
    name="lab4-pulumi-vm",
    platform_id="standard-v3",
    zone=YC_ZONE,
    resources={
        "cores": 2,
        "memory": 2,
    },
    boot_disk={
        "initialize_params": {
            "image_id": image_id,
            "size": 10,
            "type": "network-hdd",
        }
    },
    network_interfaces=[{
        "subnet_id": subnet_id,
        "nat": True,
    }],
    metadata={
        "ssh-keys": pulumi.Output.concat("ubuntu:", ssh_public_key),
    },
    opts=pulumi.ResourceOptions(provider=yandex_provider)
)

pulumi.export("vm_ip", vm.network_interfaces[0]["nat_ip_address"])
pulumi.export("ssh_command", vm.network_interfaces[0]["nat_ip_address"].apply(
    lambda ip: f"ssh -i ~/.ssh/yandex_cloud ubuntu@{ip}"
))