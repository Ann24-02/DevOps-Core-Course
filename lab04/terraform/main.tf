# Используем образ Ubuntu 22.04
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

# Используем существующую сеть
data "yandex_vpc_network" "existing" {
  name = "default"
}

data "yandex_vpc_subnet" "existing" {
  name = "default-ru-central1-a"
}

resource "yandex_compute_instance" "lab_vm" {
  name        = "lab-vm-final"
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
    }
  }

  network_interface {
    subnet_id = data.yandex_vpc_subnet.existing.id
    nat       = true
  }

  metadata = {
    user-data = "#cloud-config\nusers:\n  - name: ubuntu\n    ssh-authorized-keys:\n      - ${var.ssh_public_key}\n    sudo: ['ALL=(ALL) NOPASSWD:ALL']\n    shell: /bin/bash"
    enable-oslogin = "false"
  }
}

# Простая группа безопасности
resource "yandex_vpc_security_group" "lab_sg" {
  name        = "lab-sg-final"
  description = "Security group"
  network_id  = data.yandex_vpc_network.existing.id

  ingress {
    protocol       = "TCP"
    description    = "SSH"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

output "vm_ip" {
  value = yandex_compute_instance.lab_vm.network_interface.0.nat_ip_address
}

output "ssh_command" {
  value = "ssh -i ~/.ssh/lab5-final ubuntu@${yandex_compute_instance.lab_vm.network_interface.0.nat_ip_address}"
}