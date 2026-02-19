# Получаем последний образ Ubuntu
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts-oslogin"
}

# Получаем существующую сеть (измените имя если нужно)
data "yandex_vpc_network" "existing" {
  name = "default"  # Или название вашей существующей сети
}

# Получаем существующую подсеть (измените имя если нужно)
data "yandex_vpc_subnet" "existing" {
  name = "default-ru-central1-a"  # Или название вашей подсети
  
}

# Создаем виртуальную машину
resource "yandex_compute_instance" "lab4_vm" {
  name        = "lab4-vm"
  platform_id = "standard-v3"
  zone        = var.zone

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id = data.yandex_vpc_subnet.existing.id  # Используем существующую подсеть
    nat       = true
  }

  metadata = {
    ssh-keys = "ubuntu:${var.ssh_public_key}"
  }

  labels = {
    project = "lab4"
    tool    = "terraform"
  }
}

# Создаем группу безопасности
resource "yandex_vpc_security_group" "lab4_sg" {
  name        = "lab4-security-group"
  description = "Security group for Lab 4"
  network_id  = data.yandex_vpc_network.existing.id  # Используем существующую сеть

  ingress {
    protocol       = "TCP"
    description    = "SSH"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "App port"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    description    = "Any outgoing traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# Выходные данные
output "vm_ip" {
  description = "Public IP address of VM"
  value       = yandex_compute_instance.lab4_vm.network_interface.0.nat_ip_address
}

output "ssh_command" {
  description = "SSH connection command"
  value       = "ssh -i ~/.ssh/yandex_cloud ubuntu@${yandex_compute_instance.lab4_vm.network_interface.0.nat_ip_address}"
}

output "vm_name" {
  description = "VM name"
  value       = yandex_compute_instance.lab4_vm.name
}
