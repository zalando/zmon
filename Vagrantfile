# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

    config.vm.box = "ubuntu/trusty64"

    config.vm.hostname = "zmon"

    # ZMON Controller
    config.vm.network :forwarded_port, guest: 8080, host: 38080
    # KairosDB
    config.vm.network :forwarded_port, guest: 8084, host: 38084

    # Scheduler
    config.vm.network :forwarded_port, guest: 8085, host: 38085

    # KairosDB
    config.vm.network :forwarded_port, guest: 8083, host: 38083

    config.vm.provider "virtualbox" do |vb|
        vb.memory = 4072
        vb.cpus = 3
        vb.customize ["modifyvm", :id, "--cpuexecutioncap", "100"]
    end

    config.vm.provision "shell", path: "vagrant/setup.sh"
    config.vm.provision "shell", path: "vagrant/start.sh"

end
