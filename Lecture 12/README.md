# Lecture 12: Kubernetes Requests & Limits, LimitRange, ResourceQuotas

---


## Introduction  

### **Why Do We Need Requests and Limits?**  

![Alt text](/images/11b.png)

Imagine a Kubernetes cluster with the following setup:  
- **Node1** and **Node2**, each with **6 vCPUs and 24GB memory**.  
- **Two deployments**: `deployment-1` and `deployment-2`, each with **two pods**.  
- **Pod distribution**:  
  - `dep1-pod1` runs on **Node1**  
  - `dep1-pod2` runs on **Node2**  
  - `dep2-pod1` runs on **Node1**  
  - `dep2-pod2` runs on **Node2**  

Everything runs smoothly until **deployment-2 starts malfunctioning**. Due to a bug in its code, its pods begin consuming all available node resources, causing **resource starvation** for `deployment-1`. The malfunctioning pods take over CPU and memory, **creating a noisy neighbor problem**—where one workload unfairly affects the performance of others.

 **Solution: Requests and Limits**  
To prevent this, we use **Requests and Limits** to ensure that each pod gets its fair share of resources.  
- **Requests** define the **minimum** resources a container needs.  
- **Limits** define the **maximum** resources a container can consume.  

---

## **Benefits of Using Requests and Limits**
1. **Efficient Resource Allocation** – Ensures resources are **optimally used** across the cluster.  
2. **Avoidance of Resource Starvation** – Prevents one workload from **hogging all resources**.  
3. **Cluster Stability** – Ensures Kubernetes can efficiently **schedule and manage** workloads.  
4. **Mitigation of Noisy Neighbor Problem** – Prevents workloads from **disrupting others**.

---


## **Applying Requests and Limits to Our Example**  

![Alt text](/images/11c.png)

We define **requests and limits** as follows:  
```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1"
  limits:
    memory: "4Gi"
    cpu: "2"
```

**Understanding Node Capacity:**  
- Each node has **6 vCPUs and 24GB of memory**.  
- If each container requests **1 vCPU and 2GB of memory**, the node can accommodate up to **6 containers**.  
- Even though memory is still available, **no more workloads can be scheduled because CPU is fully allocated**.

--- 

## What are Requests and Limits?  

Kubernetes allows you to **control resource allocation** for containers using:  

| **Resource Constraint** | **Definition** | **Impact** |
|-----------------|---------------------------|----------------------------|
| **Requests** | The minimum CPU/memory a container needs. | Used by the **scheduler** to decide which node to place the Pod on. |
| **Limits** | The maximum CPU/memory a container can use. | Enforced by the **kernel**, preventing overuse. |




---

## Resource Types in Kubernetes  

The most common **resource types** in Kubernetes are:  

| **Resource**           | **Unit**               | **Example**              |
|------------------------|------------------------|--------------------------|
| **CPU**               | Cores (millicores)      | `500m` (0.5 cores)       |
| **Memory**            | Bytes (MiB/GiB)        | `512Mi`, `1Gi`           |
| **Ephemeral Storage** | Bytes (MiB/GiB)        | `500Mi`, `2Gi`           |
| **GPU**               | Vendor-specific        | `nvidia.com/gpu: 1`      |
| **HugePages**         | Bytes (2Mi, 1Gi)       | `hugepages-2Mi: 512Mi`   |
| **Custom Devices**    | Vendor-specific        | `example.com/fpga: 1`    |


Requests and limits **must be defined per container** inside a Pod.

---

## How Requests and Limits Work  

### 1️⃣ **How Requests Affect Scheduling**  

When scheduling a Pod, **Kubernetes checks requests** to determine where the Pod should run.  

Example:  
- A container requests `500m` CPU and `256Mi` memory.  
- The scheduler places it on a node that has **at least** `500m` CPU and `256Mi` memory available.  

If no such node exists, the pod remains in a **Pending state**.  

---

### 2️⃣ **How Limits Affect Running Containers**  

- **CPU Limits:** Enforced using **CPU throttling** (containers get reduced CPU cycles).  
- **Memory Limits:** Enforced using **OOM (Out of Memory) kills** (containers exceeding memory may get terminated).  

We use **"may"** in this context because **OOM (Out of Memory) kills** are not **immediately** enforced but rather **reactively** applied by the kernel when memory pressure occurs.  If there is **enough free memory**, a container **might exceed its memory limit temporarily** without being killed.

**Example:**  
- If a container has a **CPU limit of 1 core**, the kernel will **throttle CPU usage** once it reaches this limit.  
- If a container **exceeds its memory limit**, the **kernel may kill it** to free up memory.  

---

## What Happens When a Pod Exceeds Requests?  

If a container **exceeds its requested resources**, it **can still use more resources** if available on the node.  

Example:  
- A container requests **256MiB** memory but the node has **8GiB** free.  
- The container can use **more than 256MiB** because there are no strict enforcement rules for requests.  

However, **if other workloads need resources**, Kubernetes ensures at least **256MiB** remains available for this container.

---

## What Happens When a Pod Exceeds Limits?  

| **Resource** | **Behavior When Limit is Exceeded** |
|-------------|--------------------------------------|
| **CPU** | **Throttled** (restricted CPU usage). |
| **Memory** | **Killed** (Out of Memory error if memory pressure exists). |

### CPU Limits: CPU Throttling  

- If a container **exceeds its CPU limit**, the **Linux kernel throttles it**.  
- CPU is a **compressible resource**, so workloads slow down instead of failing.  

### Memory Limits: OOM Kills  

- If a container **exceeds its memory limit**, the **kernel may kill it**.  
- Memory is an **incompressible resource**, so exceeding it **results in termination**.  
- **If there is no memory pressure**, the container **may not be killed immediately**.  

---

## Monitoring Resource Utilization in Kubernetes  

To monitor the CPU and memory utilization of our nodes, we use:  

```sh
kubectl top nodes
```

However, if the **Metrics Server** is not installed, this command will fail with the following error:  

```sh
error: Metrics API not available.
```

---

## **How Kubernetes Collects “kubectl top” Metrics**

![Alt text](/images/11e.png)

1. **cAdvisor (in kubelet) samples usage**

   * cAdvisor is built into the **kubelet** and measures **CPU, memory, FS, network** for **pods/containers/nodes**.
   * Kubelet exposes these as a **summary API** at `/stats/summary`.

2. **Metrics Server scrapes kubelets**

   * **metrics-server** periodically **scrapes each kubelet’s `/stats/summary`** over TLS.
   * It keeps only **recent, in-memory** samples (no history/TSDB), and serves the **`metrics.k8s.io`** API.

3. **API server aggregation layer publishes the API**

   * The **API server’s aggregation layer** mounts metrics-server under the **`/apis/metrics.k8s.io/`** group.

4. **kubectl top queries `metrics.k8s.io`**

   * `kubectl top nodes|pods` → hits the API server → **proxied to metrics-server** → returns the latest CPU/Memory usage.

**Notes**

* This pipeline is **for live resource usage only** (not historical). Use **Prometheus** for long-term metrics.
* metrics-server **doesn’t scrape Prometheus endpoints**; it reads **kubelet summaries**.
* If metrics-server is missing or blocked (RBAC/network), `kubectl top` returns **no metrics**.

---


## **Metrics Server in EKS: Default Availability and Fallback Installation**

With the recent releases of **Amazon EKS**, the **Metrics Server is available as a managed add-on** and, in many cases, is installed **automatically** when the cluster is created — even if not explicitly defined in your `eksctl` config.

This marks a shift from earlier versions, where Metrics Server had to be manually deployed or added as an optional component.

---

### **Why This Matters**

The **Metrics Server** is a key component that enables:

* `kubectl top` commands (e.g., `kubectl top pods`, `kubectl top nodes`)
* **Horizontal Pod Autoscaler (HPA)**
* Monitoring dashboards and observability integrations

Without it, any tooling that relies on live CPU and memory usage would not function.

---

If the Metrics Server is not installed in your cluster, you can add it manually by either enabling it through the **EKS Console** under the **Add-ons** tab, or by applying the latest manifest from the official project:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```
---

## Demo: Memory Requests & Limits  

We will create a Pod named **memory-demo** with both memory requests and limits.  

### **Step 1: Define a Pod with Memory Limits**  
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: memory-demo
spec:
  containers:
    - name: memory-demo-ctr
      image: polinux/stress
      resources:
        requests:
          memory: "100Mi"
        limits:
          memory: "200Mi"
      command: ["stress"]
      args: ["--vm", "1", "--vm-bytes", "190M", "--vm-hang", "1"]
```
### **Step 2: Explanation**  
- **requests.memory: "100Mi"** → The container is guaranteed at least **100MiB of memory**.  
- **limits.memory: "200Mi"** → The container cannot exceed **200MiB**.  
- **`--vm-bytes 190M`** → Tries to allocate **190MiB of memory** (within the limit).  
- The container **will run successfully** since it does not exceed the memory limit.  

### **Step 3: Increase Memory Usage Beyond Limit**  
Now, let's modify the pod to **exceed the 200Mi limit**:  
```yaml
args: ["--vm", "1", "--vm-bytes", "250M", "--vm-hang", "1"]
```
- The container will now **be OOM killed** because it **exceeds 200MiB**.  
- Run `kubectl get pods -o wide` and `kubectl top pods` to observe the OOM kill.

#### **Why is the Container Killed Despite No Memory Pressure?**  

![Alt text](/images/11f.png)

A container **may** get terminated when it exceeds its memory limit, but **why does this happen even when the node has enough memory?**  

1. **Memory Limits are Enforced by Cgroups:**  
   - When the kubelet starts a container, it passes resource requests and limits to the **container runtime** (containerd, CRI-O, etc.).  
   - The container runtime **creates a cgroup** (Control Group) for the container, enforcing the memory constraints.  

2. **The Linux Kernel Enforces the Limit:**  
   - If a container exceeds its **memory limit**, the **cgroup OOM killer** triggers, terminating the process.  
   - This happens **independently of overall node memory availability**—the limit is per **container**, not the entire node.  

3. **Why Does the Documentation Say "MAY" Get Killed?**  
   - Some Linux configurations (e.g., overcommit settings) **may** allow memory overuse beyond limits in rare cases.  
   - However, by default, **exceeding memory limits results in an immediate OOM kill**—even if the node has free memory.  

Thus, memory limits are **hard constraints** at the container level, enforced by the **Linux kernel via cgroups**, regardless of node memory availability.

### **Step 4: Checking Assigned Requests and Limits**  

After applying the pod configurations, we can verify the assigned **requests and limits** using the following commands:  

#### **Check Requests and Limits at the Node Level**  
```sh
kubectl describe node <node-name>
```
- This displays resource allocation across all pods running on the node.  
- Look for the **Allocated resources** section to see how CPU and memory are distributed.  

#### **Check Requests and Limits at the Pod Level**  
```sh
kubectl get pod <pod-name> -o yaml
```
- This retrieves the **full manifest** of the running pod, showing assigned resource requests and limits.  

#### **Check Requests and Limits at the Deployment Level**  
```sh
kubectl describe deployment <deployment-name>
```
- This provides an overview of requests and limits set at the deployment level.  

This ensures that the configured **resource constraints are correctly applied** and helps troubleshoot scheduling or performance issues.

---

## Demo: CPU Requests & Limits  

We will create a Pod named **cpu-demo** to observe CPU throttling.  

### **Step 1: Define a Pod with CPU Limits**  
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cpu-demo
spec:
  containers:
    - name: cpu-container
      image: vish/stress
      resources:
        requests:
          cpu: "500m"
        limits:
          cpu: "900m"
      args:
        - -cpus
        - "1"
```

### **Step 2: Explanation**  
- **1 CPU = 1000m** → So `500m` means **half a CPU** and `900m` means **0.9 CPUs**.  
- The **container is allowed to use up to 900m** of CPU but will be **throttled** if it tries to exceed this.  
- Run `kubectl top pods` to observe **CPU throttling**. 

---

## Default Requests and Limits (`LimitRange`)  

If requests and limits **are not explicitly defined**, Kubernetes allows administrators to set **default values** using `LimitRange`.  

## LimitRange: Setting Default Requests and Limits  

A **LimitRange** object allows administrators to enforce **default requests and limits** for CPU and memory in a Kubernetes namespace. If a container does not specify resource requests or limits, the defaults from the LimitRange will be applied.

### LimitRange YAML Example  

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: resource-limits
  namespace: default  # Change this to your target namespace
spec:
  limits:
  - type: Container
    default:
      cpu: "2"        # Default CPU limit
      memory: "4Gi"   # Default memory limit
    defaultRequest:
      cpu: "1"        # Default CPU request
      memory: "2Gi"   # Default memory request
    max:
      cpu: "4"        # Maximum CPU a container can request
      memory: "8Gi"   # Maximum memory a container can request
    min:
      cpu: "500m"     # Minimum CPU a container must request
      memory: "512Mi" # Minimum memory a container must request
```

### Explanation  

| **Field**          | **Description** |
|--------------------|----------------|
| **`default`**      | The default resource limits applied when none are specified in the container spec. Example: A container without limits will be capped at **2 CPUs and 4Gi memory**. |
| **`defaultRequest`** | The default resource requests applied when none are defined. Example: A container will be **guaranteed 1 CPU and 2Gi memory** if no requests are set. |
| **`max`**         | The **maximum** resources a container can request. Example: A container **cannot request more than 4 CPUs or 8Gi memory**. |
| **`min`**         | The **minimum** resources a container must request. Example: A container **must request at least 500m CPU and 512Mi memory** to be scheduled. |
| **`type: Container`** | Specifies that these rules apply to **containers** within the namespace. |

---

### Applying the LimitRange  

Apply the LimitRange to a namespace using:  
```sh
kubectl apply -f limitrange.yaml
```

### Verifying the LimitRange  

To check the applied LimitRange:  
```sh
kubectl describe limitrange resource-limits
```
---

## Best Practices for Requests & Limits  

- **Always define CPU & memory requests/limits** in production workloads.  
- **Ensure memory limits match workload needs** to prevent OOM kills.  
- **Monitor resource usage** using `kubectl top pod`.  
- **Use `LimitRange`** to enforce default requests/limits for namespaces.  

---

## **Understanding Resource Quotas in Kubernetes**

In multi-tenant or shared Kubernetes clusters, it’s important to control how much **CPU, memory, storage, and other resources** a particular team, application, or namespace can consume. This is where **ResourceQuotas** come in.

### **What is a ResourceQuota?**

A `ResourceQuota` is a Kubernetes object that sets **limits on resource usage** within a specific namespace. It helps cluster administrators:

* Prevent resource exhaustion caused by runaway workloads
* Enforce fair usage policies across teams
* Establish guardrails in shared environments

ResourceQuotas apply to **pods, persistent volume claims, and other object types** in the namespace.

---

### **How It Works**

When a `ResourceQuota` is applied to a namespace:

* Any new pods, PVCs, or other quota-scoped resources **must specify resource requests/limits**
* The scheduler will **reject** or **throttle** workloads that exceed the defined quota
* Quota usage is tracked live by the Kubernetes control plane

This forces developers to **declare their resource requirements**, improving predictability and capacity planning.

---

## **Example: ResourceQuota for Namespace `app1-ns`**

Let’s apply a ResourceQuota to a namespace called `app1-ns`, restricting:

* Total number of pods
* Total number of PVCs
* Total CPU and memory usage
* Total storage requested via PVCs

---

### **1. Create the Namespace**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: app1-ns
```

---

### **2. Apply the ResourceQuota**

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: app1-quota
  namespace: app1-ns
spec:
  hard:
    pods: "10"                        # Max total number of pods in the namespace
    requests.cpu: "4"                # Total requested CPU across all pods (e.g., 4 cores)
    requests.memory: "8Gi"           # Total requested memory across all pods
    limits.cpu: "6"                  # Total max CPU allowed (limits)
    limits.memory: "12Gi"            # Total max memory allowed
    persistentvolumeclaims: "5"      # Max number of PVCs allowed
    requests.storage: "50Gi"         # Max total PVC storage requested
```

---

### **3. (Optional) LimitRange to Enforce Per-Pod Requests**

To ensure all pods in `app1-ns` specify `requests`/`limits` (required for quota enforcement), you can also apply a `LimitRange`:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-cpu-mem-limits
  namespace: app1-ns
spec:
  limits:
  - default:
      cpu: "1"
      memory: "512Mi"
    defaultRequest:
      cpu: "500m"
      memory: "256Mi"
    type: Container
```

This ensures:

* Pods **without resource definitions** get sane defaults
* All pods are quota-compliant automatically

---

## **Verifying Resource Quota**

To check current usage vs limits:

```bash
kubectl get resourcequota -n app1-ns
kubectl describe resourcequota app1-quota -n app1-ns
```

Sample output:

```
Name:       app1-quota
Namespace:  app1-ns
Resource                    Used  Hard
--------                    ----  ----
pods                        2     10
requests.cpu                1     4
requests.memory             2Gi   8Gi
limits.cpu                 1.5    6
limits.memory              4Gi    12Gi
persistentvolumeclaims      1     5
requests.storage            5Gi   50Gi
```

---

## **Summary**

| Feature                      | Benefit                                |
| ---------------------------- | -------------------------------------- |
| Enforces upper bounds        | Prevents noisy neighbors               |
| Encourages resource planning | Developers must define requests/limits |
| Works with LimitRange        | Default values if not specified        |
| Ideal for shared clusters    | Teams stay within their boundaries     |

---

