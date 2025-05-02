import os

filename = "agent_monitor.c"
ebpf_code = '''\
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("tracepoint/syscalls/sys_enter_execve")
int trace_execve(void *ctx) {
    bpf_printk("execve called\\n");
    return 0;
}

char _license[] SEC("license") = "GPL";
'''

if not os.path.exists(filename):
    with open(filename, "w") as f:
        f.write(ebpf_code)
    print(f"{filename} created successfully.")
else:
    print(f"{filename} already exists.")
