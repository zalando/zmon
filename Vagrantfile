# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

    config.vm.box = "ubuntu/zesty64"

    config.vm.hostname = "zmon"

    # Controller
    config.vm.network :forwarded_port, guest: 8080, host: 38080
    config.vm.network :forwarded_port, guest: 8443, host: 8443

    # EventLog Service
    config.vm.network :forwarded_port, guest: 8081, host: 38081

    # KairosDB
    config.vm.network :forwarded_port, guest: 8083, host: 38083

    # Scheduler
    config.vm.network :forwarded_port, guest: 8085, host: 38085

    # Redis
    config.vm.network :forwarded_port, guest: 6379, host: 38086

    # PostgreSQL
    config.vm.network :forwarded_port, guest: 5432, host: 38088

    config.vm.provider "virtualbox" do |vb|
        vb.name = "ZMON-DEMO"
        vb.memory = 4600
        vb.cpus = 3
        vb.customize ["modifyvm", :id, "--cpuexecutioncap", "100"]
    end

    config.vm.provision "shell", path: "vagrant/setup.sh"
    config.vm.provision "shell", path: "vagrant/start.sh"

end
