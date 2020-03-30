import paramiko

try:
    ssh_client = paramiko.SSHClient()                                   # create SSHClient instance
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())    # AutoAddPolicy automatically adding the server_ip and new host key
    ssh_client.load_system_host_keys()

    ssh_client.connect("10.10.30.5", 22, 'rh', 'P@55w0rD!')

    command ='ls -la'
    stdin, stdout, stderr = ssh_client.exec_command(command)
    #print(str(stdin.read()))
    #print(str(stdout.read()))
    print('success')


except:
    print('error')
