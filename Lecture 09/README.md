# Lecture 08: Lecture 9: CSI & Amazon EBS with EKS

---

# **Introduction**  
Kubernetes is built on a **modular and extensible architecture**, where the **core components** (Control Plane and Node Components) handle fundamental orchestration tasks, while **plugins, add-ons, and third-party extensions** enhance functionality without bloating the system. This lecture explores the **Kubernetes Core**, its **plugin-based architecture**, and key extension mechanisms like **CNI (networking), CSI (storage), and CRI (container runtimes)**. We’ll also discuss how this design ensures **scalability, flexibility, and vendor neutrality**, enabling seamless integration with diverse cloud-native tools.  

---

# **Kubernetes Core and Extended Architecture**  

![Alt text](/images/9a.png)

Kubernetes is a powerful container orchestration platform built on a **modular design**. This modularity enables **flexibility, scalability, and extensibility**. The **core components** handle essential orchestration tasks, while **plugins, add-ons, and third-party extensions** extend functionality without bloating the core system.  

This section clarifies the distinction between **Kubernetes Core** and **External Extensions**, explaining how various components interact within the overall architecture.  

---

## **Kubernetes Core Architecture**  

### **What is Kubernetes Core?**  
The **Kubernetes Core** consists of essential built-in components responsible for cluster management and orchestration. These components are categorized into **Control Plane Components** and **Node Components**.  

### **1️⃣ Control Plane Components**  
The control plane manages cluster operations, making scheduling decisions and maintaining the desired state.  

- **API Server:** The central control plane component that validates and processes REST API requests, enforcing security policies and forwarding requests to relevant components.  
- **Scheduler:** Assigns Pods to nodes based on resource availability and scheduling policies.  
- **Controller Manager:** Runs control loops to maintain the desired state (e.g., replication, endpoint management).  
- **etcd:** A distributed, consistent key-value store that persistently stores all cluster state and configuration data.  
- **Cloud Controller Manager:** Manages cloud-provider-specific integrations such as external load balancers, persistent storage provisioning, and node lifecycle management.  

### **2️⃣ Node Components**  
Nodes are the worker machines that run containerized workloads.  

- **kubelet:** The primary node agent that ensures containers are running as expected.  
- **kube-proxy:** Maintains network rules on each node, enabling seamless service discovery and communication between Pods.  

---

## **Kubernetes Extensions: Beyond the Core**  
While the **Kubernetes Core** provides essential orchestration functionalities, additional features like networking, storage, monitoring, and security are implemented via **external components**.  

### **1️⃣ Plugins**  

![Alt text](/images/9b.png)

Plugins extend Kubernetes by enabling external integration while adhering to standardized APIs. 


CNI (Container Network Interface), CRI (Container Runtime Interface), and CSI (Container Storage Interface) are standardized interfaces that define how networking, runtime, and storage components interoperate with Kubernetes. These interfaces adhere to specifications that are developed and maintained by the Kubernetes community under the governance of the CNCF. Although the CNCF endorses these standards, it is the community that actively defines and updates the specifications.

Anyone can develop their own plugins for CNI, CRI, and CSI as long as they conform to these specifications, ensuring compatibility and interoperability within Kubernetes environments.


- **Container Network Interface (CNI):** Configures Pod networking and IP allocation.  
- **Container Storage Interface (CSI):** Manages external storage solutions.  
- **Container Runtime Interface (CRI):** Allows Kubernetes to interact with various container runtimes (e.g., containerd, CRI-O).  
 

#### **CRI Plugins (Container Runtimes)**
*(The following list is indicative, not exhaustive.)*
| Plugin        | Description |
|--------------|------------|
| **containerd** | Default for most Kubernetes setups; lightweight, optimized, and follows OCI standards. |
| **CRI-O** | Minimal runtime designed for Kubernetes; integrates tightly with OpenShift. |
| **Kata Containers** | Uses lightweight VMs for security; ideal for isolating untrusted workloads. |
| **gVisor (by Google)** | User-space sandboxing for enhanced security; limits direct host access. |

#### **CNI Plugins (Networking)**
*(The following list is indicative, not exhaustive.)*
| Plugin        | Description |
|--------------|------------|
| **Calico** | Supports network policies and BGP routing; ideal for security-focused environments. |
| **Cilium** | High-performance with eBPF-based networking; excels in observability and security. |
| **Flannel** | Lightweight and simple; lacks network policy support. |
| **Weave Net** | Provides encrypted pod-to-pod communication; supports multi-cluster setups. | 

#### **CSI Plugins (Storage)**
*(The following list is indicative, not exhaustive.)*
| Plugin        | Description |
|--------------|------------|
| **Amazon EBS CSI** | Provides block storage for Kubernetes workloads on AWS; supports dynamic provisioning. |
| **Azure Disk CSI** | Offers high-performance, persistent storage for Kubernetes on Azure. |
| **Google PD CSI** | Integrates with Google Cloud Persistent Disks; supports snapshots and resizing. |
| **Ceph RBD CSI** | Ideal for scalable, distributed storage; supports snapshots and cloning. |
| **Portworx CSI** | Enterprise-grade storage with high availability, backups, and replication. |
| **OpenEBS CSI** | Lightweight and cloud-native storage for Kubernetes; optimized for local PVs. |
| **Longhorn CSI** | Rancher’s distributed block storage for Kubernetes; supports snapshots and disaster recovery. |

---

#### **Responsibilities of CRI, CNI, and CSI in Kubernetes**  
*(The responsibilities listed below are indicative, not exhaustive.)*  

**CRI (Container Runtime Interface) - Manages Container Lifecycle**  
- Pulls container images from registries.  
- Starts, stops, and deletes containers.  
- Manages container networking via CNI integration.  
- Handles logging and monitoring of containers.  
- Allocates resources like CPU and memory to containers.  
- Ensures compatibility with Kubernetes via standardized gRPC APIs.  

**CNI (Container Network Interface) - Manages Pod Networking**  
- Assigns IP addresses to pods.  
- Enables communication between pods across nodes.  
- Manages network policies for security and isolation.  
- Supports service discovery and DNS resolution.  
- Integrates with cloud and on-prem networking solutions.  
- Provides network metrics and observability features.  

**CSI (Container Storage Interface) - Manages Storage for Pods**  
- Dynamically provisions persistent storage for workloads.  
- Supports mounting and unmounting of storage volumes.  
- Handles volume resizing, snapshots, and backups.  
- Ensures data persistence across pod restarts.  
- Integrates with various cloud and on-prem storage providers.  
- Manages access controls and multi-node storage sharing.  


### **2️⃣ Add-Ons**  
Add-ons enhance Kubernetes with additional functionalities:  

- **Ingress Controllers:** Handle external access, load balancing, and routing.  
- **Monitoring Tools:** Observability tools like Prometheus and Grafana.  
- **Service Meshes:** Solutions like Istio and Linkerd enhance inter-service communication.  

### **3️⃣ Third-Party Extensions**  
Third-party tools and solutions integrate seamlessly into Kubernetes:  

- **Helm:** Kubernetes package manager for simplified deployment.  
- **Prometheus:** Monitoring and alerting system for cloud-native applications.  
- **Istio:** Service mesh for security, traffic management, and observability.  

---

## **Deep Dive into Kubernetes Interfaces**  
Kubernetes uses standardized interfaces for seamless extensibility. The three primary interfaces are **CSI, CNI, and CRI**, each designed to manage storage, networking, and runtime integration.  

### **Overview of Kubernetes Interfaces**  

| **Interface** | **Purpose** | **Key Features** | **Common Implementations** |  
|--------------|------------|------------------|---------------------------|  
| **Container Storage Interface (CSI)** | Enables external storage integration without modifying Kubernetes core. | - Decouples storage drivers from Kubernetes. <br> - Supports snapshots, volume expansion, and lifecycle management. <br> - Uses gRPC-based APIs (`CreateVolume`, `DeleteVolume`, etc.). | - AWS EBS CSI Driver <br> - GCE Persistent Disk CSI Driver <br> - Ceph RBD CSI Driver |  
| **Container Network Interface (CNI)** | Standardizes how Kubernetes manages networking. | - Configures Pod networking and IP allocation. <br> - Supports network policies and encryption. <br> - Enables scalable and secure communication. | - Calico (Network policies) <br> - Cilium (eBPF-based performance) <br> - AWS VPC CNI (AWS-native networking) <br> - Weave Net (Encrypted multi-cluster networking) |  
| **Container Runtime Interface (CRI)** | Defines how Kubernetes interacts with different container runtimes. | - Manages container lifecycle (image pulling, creation, execution, logging). <br> - Ensures runtime consistency. <br> - Enables Kubernetes to work with multiple runtimes. | - containerd (Lightweight, Kubernetes-native) <br> - CRI-O (Minimal runtime for Kubernetes) <br> - Podman (Daemonless alternative) <br> - Docker (Previously supported via dockershim; now deprecated) |  

---

## **Why Kubernetes Uses a Plugin-Based Architecture?**  

Kubernetes’ **plugin-based architecture** is fundamental to its flexibility, scalability, and vendor neutrality. Here’s why:  

- **Interoperability:** Kubernetes interacts with various **networking, storage, and runtime solutions** without tight integration into its core.  
- **Flexibility & Vendor Neutrality:** Users can select the **best tools for their workloads** without being locked into a specific vendor.  
- **Encourages Innovation:** Plugin developers can **iterate and improve** their solutions independently, without requiring changes to Kubernetes itself.  
- **Scalability & Maintainability:** Individual components can be **scaled and upgraded independently**, improving reliability and maintainability.  

For example, **Cilium**, a CNI plugin using **eBPF**, enhances network security and observability without requiring modifications to Kubernetes' core networking model. This level of extensibility allows Kubernetes to adapt seamlessly across different infrastructure environments.  

---

## Evolution of Storage in Kubernetes: From In-Tree to CSI Drivers

![Alt text](/images/9c.png)

Managing **persistent storage** in Kubernetes has come a long way. Initially, storage drivers were built directly into Kubernetes' core codebase, known as **in-tree volume plugins**. Over time, this tightly coupled model proved limiting, leading to the adoption of the **Container Storage Interface (CSI)**—a modular and extensible solution for storage integration.

This write-up explores the transition from in-tree plugins to CSI drivers and explains where commonly-used storage types fit into Kubernetes today.

---

## 1. In-Tree Volume Plugins: The Legacy Model

In-tree volume plugins were integrated directly into Kubernetes' codebase. Adding or updating these plugins required modifying Kubernetes itself, resulting in several drawbacks:

- Maintenance was cumbersome and tied to Kubernetes release cycles.
- Vendors could not independently develop or release updates.
- Bugs in storage drivers could affect Kubernetes core functionality.

### Examples of In-Tree Plugins:
- `awsElasticBlockStore` (AWS EBS)
- `azureDisk`, `azureFile`
- `gcePersistentDisk` (GCE PD)
- `nfs`, `glusterfs`
- `rbd` (Ceph RADOS Block Device)
- `iscsi`, `fc` (Fibre Channel)

**Note:** Most in-tree plugins are deprecated and replaced with CSI drivers.

---

## 2. Container Storage Interface (CSI): The Modern Standard

To address the limitations of in-tree plugins, Kubernetes adopted the **Container Storage Interface (CSI)**, developed by the **Cloud Native Computing Foundation (CNCF)**. CSI decouples storage driver development from Kubernetes core, allowing vendors to independently create and maintain their drivers.

### Key Benefits of CSI:
- **Independent updates:** Vendors can release drivers without waiting for Kubernetes updates.
- **Faster development:** Features and fixes are delivered more quickly.
- **Flexibility:** CSI supports advanced capabilities like snapshotting, resizing, cloning, and monitoring.
- **Easy integration:** Drivers for custom use cases can be developed with ease.

### Examples of CSI Drivers:
- AWS EBS CSI Driver: `ebs.csi.aws.com`
- GCE PD CSI Driver: `pd.csi.storage.gke.io`
- Azure Disk CSI Driver: `disk.csi.azure.com`
- Ceph CSI Driver
- OpenEBS CSI Drivers (e.g., for cStor, Jiva, etc.)
- Portworx CSI, vSphere CSI

**Note:** Starting with Kubernetes 1.21, most in-tree volume plugins were officially deprecated, and CSI became the default for handling persistent volumes.

---

#### **Transitioning from In-Tree Drivers**
While in-tree drivers served their purpose in the early stages of Kubernetes, they are now being deprecated. CSI plugins are the recommended approach for modern storage management. For example:

**In-Tree Driver Example**:
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: in-tree-pv
  # Name of the PersistentVolume resource.
spec:
  capacity:
    storage: 10Gi
    # Defines the size of the volume. This PV provides 10Gi of storage.
  accessModes:
    - ReadWriteOnce
    # The volume can be mounted as read-write by a single node.
  awsElasticBlockStore:
    # This is the legacy in-tree volume plugin for AWS EBS.
    # It allows mounting an existing AWS EBS volume into a pod.
    volumeID: vol-0abcd1234efgh5678
    # The unique ID of the EBS volume to be mounted.
    fsType: ext4
    # The filesystem type of the volume. This must match the filesystem on the EBS volume.

```

**CSI Driver Example**:
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: csi-pv
  # The name of the PersistentVolume resource.
spec:
  capacity:
    storage: 10Gi
    # Defines the storage size of the volume. This volume offers 10Gi of space.
  accessModes:
    - ReadWriteOnce
    # The volume can be mounted as read-write by only one node at a time.
  storageClassName: gp3-sc
  # The StorageClass to which this volume belongs.
  # This allows dynamic provisioning and matching with a PVC that requests 'gp3-sc'.
  csi:
    # This specifies the use of a Container Storage Interface (CSI) driver,
    # which is the recommended way to provision external storage in modern Kubernetes clusters.
    driver: ebs.csi.aws.com
    # The name of the CSI driver used for AWS EBS volumes.
    volumeHandle: vol-0abcd1234efgh5678
    # The unique ID of the EBS volume in AWS.
    # This is used by the driver to locate and attach the correct volume.
    fsType: ext4
    # The filesystem type to mount. This must match the actual filesystem on the EBS volume.

```

---

#### **Key Takeaways:**
1. **In-Tree Drivers**: These legacy solutions are tightly coupled with Kubernetes and being phased out.  
2. **CSI Plugins**: The preferred method for storage integration, offering scalability and extensibility.  
3. **Dynamic Provisioning**: CSI supports automated volume creation and lifecycle management via StorageClasses.  
4. **File, Block, and Object Storage**:
   - **File and Block Storage**: Mountable as volumes in Pods using CSI plugins.  
   - **Object Storage**: Not natively mountable; access via application-level SDKs or APIs is recommended.

---

Kubernetes supports **CSI (Container Storage Interface) plugins** for both **file (NFS)** and **block storage** options. These plugins are provided by storage vendors such as **NetApp**, **Dell EMC**, and cloud providers like **AWS**, **Azure**, and **Google Cloud Platform (GCP)**. CSI plugins enable Kubernetes Pods to access file and block storage seamlessly, offering advanced features like dynamic provisioning, snapshots, and volume resizing.

For object storage solutions like **Amazon S3**, **Azure Blob Storage**, or **Google Cloud Storage (GCS)**, Kubernetes does not natively support mounting object storage as volumes because object storage operates differently from file systems. Instead, it is **recommended to use application-specific SDKs** or APIs to interact with object storage. These SDKs allow applications to efficiently access and manage object storage for tasks such as retrieving files, uploading data, and performing operations like versioning or replication.

The distinction lies in the use case:  
- **File and Block Storage**: Designed for direct mounting and integration with Kubernetes workloads using CSI plugins.  
- **Object Storage**: Better suited for application-level access via APIs or SDKs, as it was not designed to be mounted like file systems.  

By leveraging CSI plugins for file and block storage, and SDKs for object storage, you can make the most of modern, scalable storage options tailored to your Kubernetes workloads.

> Earlier, Kubernetes supported a lot of built-in drivers, called in-tree plugins. But today, the ecosystem has fully moved to **CSI drivers**, which are the future-proof way to provision and consume persistent storage. So whatever storage you’re dealing with — AWS EBS, NFS, iSCSI — if you’re doing it the modern way, you’re doing it with a **CSI driver**.

---

### What is Amazon Elastic Block Store (EBS)?

Amazon EBS is a block-level storage service provided by AWS. It offers **persistent and high-performance storage** for Amazon EC2 instances, suitable for use cases like **databases, file systems, and other data-intensive applications**.

EBS supports multiple volume types with varying performance and cost characteristics:

* **gp2 / gp3** – General Purpose SSD (balanced price/performance)
* **io1 / io2** – Provisioned IOPS SSD (high-performance, mission-critical workloads)
* **st1** – Throughput-Optimized HDD (for large, sequential workloads)
* **sc1** – Cold HDD (lowest cost for infrequently accessed data)

---

### Installing the AWS EBS CSI Driver

The **EBS CSI (Container Storage Interface) driver** allows Kubernetes to dynamically provision and manage Amazon EBS volumes as persistent volumes (PVs).

#### Step 1: Attach IAM Policy to Worker Node Role

📘 Refer: [EBS CSI Driver Install Guide](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/master/docs/install.md)

To allow worker nodes to interact with Amazon EBS on behalf of Kubernetes workloads, the correct IAM permissions must be attached.

* AWS provides a **managed policy** named `AmazonEBSCSIDriverPolicy`.
* This policy should be attached to the **IAM role associated with your worker nodes**.

🔍 **Find your worker node role:**

```bash
kubectl -n kube-system describe configmap aws-auth
```

Look for the `rolearn` entry—something like:

```
eksctl-eks-cluster-1-nodegroup-ng--NodeInstanceRole-pKiAt45pKVKj
```

📌 Navigate to the AWS Console → IAM → Roles → Search for this role → Attach the `AmazonEBSCSIDriverPolicy`.

#### Step 2: Install the EBS CSI Driver

```bash
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.44"
```

#### Observations After Installation

Check what was deployed:

```bash
kubectl get pods -n kube-system
```

You’ll see:

* **DaemonSet:** `ebs-csi-node`
  → Runs on **every node**, handling local volume lifecycle events (mount, unmount, etc.)

* **Deployment:** `ebs-csi-controller`
  → A centralized controller that interacts with the **AWS APIs** to provision and manage EBS volumes.

---

### Key Concepts to Remember

* **`ebs-csi-node` DaemonSet:** Ensures volume operations are handled on **each worker node**.
* **`ebs-csi-controller` Deployment:** Manages cluster-wide volume provisioning and interacts with AWS to create and attach EBS volumes.
* **DaemonSet behavior:**
  In EKS, DaemonSet pods are scheduled on worker nodes only (since control plane is managed). In a self-managed cluster, you might also see them on control plane nodes.

---

### Persistent Volumes (PVs) & Persistent Volume Claims (PVCs)

![Alt text](/images/9d.png)
#### **Persistent Volumes (PVs)**

- **What is a PV?**  
  A PV is a piece of storage in your cluster that has been provisioned either manually by an administrator or dynamically using Storage Classes.
  
- **Key Characteristics:**  
  PVs exist independently of Pod lifecycles and can be reused or retained even after the Pod is deleted. They have properties such as **capacity, access modes, and reclaim policies**.

#### **Persistent Volume Claims (PVCs)**

- **What is a PVC?**  
  A PVC is a request for storage by a user. It functions similarly to how a Pod requests compute resources. When a PVC is created, Kubernetes searches for a PV that meets the claim's requirements.
  
- **Binding Process:**  
  1. **Administrator:** Provisions PVs (or sets up Storage Classes for dynamic provisioning).  
  2. **Developer:** Creates a PVC in the Pod specification requesting specific storage attributes.  
  3. **Kubernetes:** Binds the PVC to a suitable PV, thereby making the storage available to the Pod.


**Pods rely on Node resources—such as CPU, memory, and network—to run containers.** On the other hand, when a Pod requires **persistent storage**, it uses a **PersistentVolumeClaim (PVC)** to request storage from a **PersistentVolume (PV)**, which serves as the **actual storage backend**. This separation of compute and storage allows Kubernetes to manage them independently, improving flexibility and scalability.

---

### **Understanding Scope & Relationships of PV and PVC in Kubernetes**

In Kubernetes, **PersistentVolumes (PVs)** and **PersistentVolumeClaims (PVCs)** play a central role in persistent storage — but they differ in how they're scoped and used.

![Alt text](/images/9e.png)

#### **PVs are Cluster-Scoped Resources**
- A **PersistentVolume (PV)** is a **cluster-wide resource**, just like Nodes or StorageClasses.
- This means it is **not tied to any specific namespace**, and it can be viewed or managed from anywhere within the cluster.
- You can verify this using:
  ```bash
  kubectl api-resources | grep persistentvolume
  ```
  This shows that the resource `persistentvolumes` has **no namespace**, indicating it's **cluster-scoped**.

#### **PVCs are Namespace-Scoped**
- A **PersistentVolumeClaim (PVC)**, on the other hand, is a **namespaced resource**, just like Pods or Deployments.
- This means it exists **within a specific namespace** and is only accessible by workloads (Pods) within that namespace.
- You can verify this using:
  ```bash
  kubectl api-resources | grep persistentvolumeclaim
  ```
  This shows that `persistentvolumeclaims` are scoped within a namespace.

---

### **Why Is This Important?**

Let’s say you have a namespace called `app1-ns`. If a PVC is created in `app1-ns` and binds to a PV, **only Pods in `app1-ns` can use that PVC**.

If a Pod in `app2-ns` tries to reference the same PVC, it will fail — because the PVC is invisible and inaccessible outside its namespace.

---

### **1-to-1 Binding Relationship Between PVC and PV**

- A **PVC can bind to only one PV**.
- Similarly, **a PV can be bound to only one PVC**.
- This is a **strict one-to-one relationship**, ensuring data integrity and predictable access control.
- Once a PV is bound, its `claimRef` field is populated, and it cannot be claimed by any other PVC unless explicitly released.

> **`claimRef`** is a field in a **PersistentVolume (PV)** that records which **PersistentVolumeClaim (PVC)** has successfully claimed it. It includes details like the PVC’s name and namespace. This field ensures that the PV is not mistakenly claimed by any other PVC, enforcing a **one-to-one binding** between the PV and its assigned PVC.

---

### **Additional Key Points**
- **PVCs request storage**; PVs **fulfill that request** if they match capacity, access mode, and storage class.
- Once a PVC is bound, **it remains bound** until:
  - The PVC is deleted.
  - The PV is manually reclaimed or deleted (depending on the reclaim policy).
- The reclaim policy (`Retain`, `Delete`, or deprecated `Recycle`) determines what happens to the PV after the PVC is deleted.

---

### **Example Scenario**

Let’s say:
- You create a PVC named `data-pvc` in the namespace `app1-ns`.
- It binds to a cluster-scoped PV.
- Only **Pods in `app1-ns`** can now reference this PVC.

If a Pod in `app2-ns` tries to mount this PVC, it will result in an error like:
```
persistentvolumeclaims "data-pvc" not found
```

Because from `app2-ns`'s perspective, that PVC does not exist.

---

### **Kubernetes Persistent Storage Flow (Manual Provisioning)**

![Alt text](/images/9f.png)

| **Step** | **Role**                | **Action**                                                                                          | **Details / Notes**                                                                 |
|----------|-------------------------|------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| 1        | **Developer**           | Requests 5Gi persistent storage for a Pod.                                                           | May request via a PVC or through communication with the Kubernetes Admin.          |
| 2        | **Kubernetes Admin**    | Coordinates with Storage Admin for backend volume.                                                  | Backend storage could be SAN/NAS exposed via iSCSI, NFS, etc.                      |
| 3        | **Storage Admin**       | Allocates a physical volume from a 500Ti storage pool.                                               | May involve LUN creation, NFS export, etc., based on the infrastructure.            |
| 4        | **Kubernetes Admin**    | Creates a **PersistentVolume (PV)** representing the physical volume in Kubernetes.                 | Specifies capacity, `accessModes`, `volumeMode`, `storageClassName`, etc.          |
| 5        | **Developer**           | Creates a **PersistentVolumeClaim (PVC)** requesting 5Gi with specific access and volume modes.     | PVC must match criteria defined in the PV.                                          |
| 6        | **Kubernetes**          | Binds PVC to a suitable PV if all parameters match.                                                 | Matching criteria include: storage class, access mode, volume mode, size, etc.     |
| 7        | **Pod**                 | References the PVC in its volume definition and mounts it in a container.                          | PVC acts as an abstraction; Pod doesn’t interact with the PV directly.             |

---

### **Important Notes**

- **PV** is a **cluster-scoped** resource.
- **PVC** is a **namespaced** resource.
- One **PV can be claimed by only one PVC** (1:1 relationship).
- The Pod must be in the **same namespace** as the PVC it is using.
- Communication with physical storage is handled by either:
  - **In-tree drivers** (legacy; e.g., `awsElasticBlockStore`, `azureDisk`)
  - **CSI drivers** (modern; e.g., `ebs.csi.aws.com`, `azurefile.csi.azure.com`)

> In many cases, developers are well-versed with Kubernetes and can handle the creation of **PersistentVolumeClaims (PVCs)** themselves. With the introduction of **StorageClasses**, the process of provisioning **PersistentVolumes (PVs)** has been **automated**—eliminating the need for Kubernetes administrators to manually coordinate with storage admins and pre-create PVs. When a PVC is created with a **StorageClass**, Kubernetes **dynamically provisions** the corresponding PV. We’ll explore StorageClasses in detail shortly.

---

#### **Access Modes in Kubernetes Persistent Volumes**

Persistent storage in Kubernetes supports various access modes that dictate how a volume can be mounted. Access modes essentially govern how the volume is mounted across **nodes**, which is critical in clustered environments like Kubernetes.
 

| **Access Mode**          | **Description**                                                                                          | **Example Use Case**                                            | **Type of Storage & Examples** |
|--------------------------|----------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|--------------------------------|
| **ReadWriteOnce (RWO)**  | The volume can be mounted as read-write by a **single node**. Multiple Pods can access it **only if** they are on the same node. | Databases that require exclusive access but may run multiple replicas per node.  | **Block Storage** (e.g., Amazon EBS, GCP Persistent Disk, Azure Managed Disks) |
| **ReadOnlyMany (ROX)**   | The volume can be mounted as **read-only** by **multiple nodes** simultaneously.                        | Sharing static data like configuration files or read-only datasets across multiple nodes. | **File Storage** (e.g., NFS, Azure File Storage) |
| **ReadWriteMany (RWX)**  | The volume can be mounted as **read-write** by **multiple nodes** simultaneously.                       | Content management systems, shared data applications, or log aggregation. | **File Storage** (e.g., Amazon EFS, Azure File Storage, On-Prem NFS) |
| **ReadWriteOncePod (RWOP)** (Introduced in v1.29) | The volume can be mounted as read-write by **only one Pod across the entire cluster**.                 | Ensuring exclusive access to a volume for a single Pod, such as in tightly controlled workloads. | **Block Storage** (e.g., Amazon EBS with `ReadWriteOncePod` enforcement) |

---

### **Explanation of Storage Types**

#### **Block Storage**  
Block storage is ideal for databases and applications requiring **low-latency, high-performance storage**. It provides raw storage blocks that applications can format and manage as individual disks.  
- **Examples**: Amazon EBS, GCP Persistent Disk, Dell EMC Block Storage.  
- **Key Characteristic**: Block storage is generally **node-specific** and does not support simultaneous multi-node access.  
- **Access Modes**: Commonly used with `ReadWriteOnce` or `ReadWriteOncePod`, as these modes restrict access to a single node or Pod at a time.

*Analogy*: Block storage is like attaching a USB drive to a single computer—it provides fast, reliable storage but cannot be shared concurrently across multiple systems.

---

#### **File Storage**  
File storage is designed for **shared storage scenarios**, where multiple Pods or applications need simultaneous access to the same data. It is mounted as a shared filesystem, making it ideal for distributed workloads.  
- **Examples**: Amazon EFS, Azure File Storage, On-Prem NFS (Network File System).  
- **Key Characteristic**: File storage is purpose-built for **multi-node concurrent access**.  
- **Access Modes**: File storage often supports modes like `ReadOnlyMany` or `ReadWriteMany`, allowing multiple Pods—across different nodes—to read from and write to the same volume.

*Analogy*: File storage works like a network drive, where multiple systems can access, update, and share files simultaneously.

---

### **Key Differences: Block Storage vs. File Storage**
1. **Multi-Node Access**: Block storage is single-node focused, whereas file storage allows concurrent access across multiple nodes.  
2. **Access Modes**: `ReadWriteOnce` or `ReadWriteOncePod` are typical for block storage, while `ReadWriteMany` is common for file storage due to its multi-node capabilities.  
3. **Use Cases**:  
   - **Block Storage**: Databases, transactional systems, or workloads requiring exclusive and high-performance storage.  
   - **File Storage**: Shared workloads like web servers, content management systems, and applications requiring shared configurations or assets.

When evaluating storage options, it's important to align the access modes and storage type with the needs of the workload. For example, "Many" in an access mode (`ReadOnlyMany` or `ReadWriteMany`) usually signals that the underlying storage is file-based and optimized for shared use.

---


### **Reclaim Policies in Kubernetes**  

Reclaim policies define what happens to a **PersistentVolume (PV)** when its bound **PersistentVolumeClaim (PVC)** is deleted. The available policies are:  


#### **1. Delete (Common for Dynamically Provisioned Storage)**  
- When the PVC is deleted, the corresponding PV and its underlying **storage resource** (e.g., cloud disk, block storage) are **automatically deleted**.  
- This is useful in **cloud environments** where storage resources should be freed when no longer in use.  

**🔹 Example Use Case:**  
- **AWS EBS, GCP Persistent Disk, Azure Disk** – Storage dynamically provisioned via CSI drivers gets deleted along with the PV, preventing orphaned resources.  

---

#### **2. Retain (Manual Intervention Needed for Reuse)**  
- When the PVC is deleted, the PV remains in the cluster but moves to a **"Released"** state.  
- **The data is preserved**, and manual intervention is required to either:  
  - Delete and clean up the volume.  
  - Rebind it to another PVC by manually removing the claim reference (`claimRef`).  

**🔹 Example Use Case:**  
- **Auditing & Compliance:** Ensures data is retained for logs, backups, or forensic analysis.  
- **Manual Data Recovery:** Useful in scenarios where storage should not be automatically deleted after PVC removal.  

---

#### **3. Recycle (Deprecated in Kubernetes v1.20+)**  
- This policy would automatically **wipe the data** (using a basic `rm -rf` command) and make the PV available for new claims.  
- It was removed in favor of **dynamic provisioning** and more secure, customizable cleanup methods.  

**🔹 Why Deprecated?**  
- Lacked customization for **secure erasure** methods.  
- Didn't support advanced cleanup operations (e.g., snapshot-based restoration).  

---

### **Choosing the Right Reclaim Policy**  

| **Reclaim Policy** | **Behavior** | **Best Use Case** | **Common in** |
|-------------------|------------|-----------------|----------------|
| **Delete** | Deletes PV and storage resource when PVC is deleted. | Cloud-based dynamically provisioned storage. | AWS EBS, GCP PD, Azure Disk. |
| **Retain** | Keeps PV and storage, requiring manual cleanup. | Backup, auditing, manual data recovery. | On-prem storage, long-term retention workloads. |
| **Recycle (Deprecated)** | Cleans volume and makes PV available again. | (Not recommended) | Previously used in legacy systems. |


---

### **PVC and PV Binding Conditions**  

For a **PersistentVolumeClaim (PVC)** to bind with a **PersistentVolume (PV)** in Kubernetes, the following conditions must be met:  

- **Matching Storage Class**  
  - The `storageClassName` of the PVC and PV must match.  
  - If the PVC does not specify a storage class, it can bind to a PV **without a storage class**.  

- **Access Mode Compatibility**  
  - The access mode requested by the PVC (`ReadWriteOnce`, `ReadOnlyMany`, `ReadWriteMany`) **must be supported** by the PV.  

- **Sufficient Storage Capacity**  
  - The PV’s storage **must be equal to or greater than** the requested capacity in the PVC.  

- **Volume Binding Mode**  
  - If set to `Immediate`, the PV binds as soon as a matching PVC is found.  
  - If set to `WaitForFirstConsumer`, binding happens **only when a pod** using the PVC is scheduled.  

- **PV Must Be Available**  
  - The PV must be in the `Available` state (i.e., not already bound to another PVC).  
  - If the PV is already bound, it **cannot** be reused unless manually released.  

- **Matching Volume Mode**

    **Volume Modes** define how a Persistent Volume (PV) is presented to a Pod:
    1. **Block**: Provides raw, unformatted storage for the Pod. The application handles formatting and usage.  
    2. **Filesystem**: Presents a formatted volume, ready for file-level operations.  

    **Matching Modes**:  
    - A PVC requesting `volumeMode: Block` must match a PV with `volumeMode: Block`.  
    - A PVC requesting `volumeMode: Filesystem` must match a PV with `volumeMode: Filesystem`.

    **Use Case for `volumeMode: Block`**: This is typically used when an application, such as a database (e.g., PostgreSQL, MySQL), needs direct control over disk formatting, partitioning, or low-level I/O optimizations.

    This ensures compatibility between Pods and their storage. 

- **Claim Reference (Manual Binding Cases)**  
  - If the PV has a `claimRef` field, it can **only bind** to the specific PVC mentioned in that field.  

These conditions ensure a **seamless** and **reliable** binding process, providing persistent storage to Kubernetes workloads.  

---

### **Summary Table: PVC and PV Binding Conditions**  

| **Condition**              | **Requirement for Binding**                                             |
|----------------------------|-------------------------------------------------------------------------|
| **Storage Class Match**     | `storageClassName` of PVC and PV must match (or both can be empty).   |
| **Access Mode Compatibility** | PVC’s requested access mode must be supported by PV.                 |
| **Sufficient Capacity**     | PV’s storage must be **≥** PVC’s requested capacity.                 |
| **Volume Binding Mode**     | Either `Immediate` or `WaitForFirstConsumer`.                         |
| **Volume State**           | PV must be in `Available` state to bind.                             |
| **Matching Volume Mode**    | PVC and PV must have the same `volumeMode` (`Filesystem` or `Block`). |
| **Claim Reference**         | If PV has a `claimRef`, it can only bind to that specific PVC.        |

---

### **Example Table: PVC vs. PV Matching**  

| **Condition**       | **PVC Requirement** | **PV Must Have**        |
|--------------------|---------------------|-------------------------|
| **Storage Capacity** | `size: 10Gi`        | `size ≥ 10Gi`           |
| **Access Mode**      | `ReadWriteMany`     | `ReadWriteMany`         |
| **Storage Class**    | `fast-ssd`          | `fast-ssd`              |
| **Volume State**     | `Unbound`           | `Available`             |
| **Volume Mode**      | `Filesystem`        | `Filesystem`            |

---


### **Demo: Persistent Volumes and PVCs with Reclaim Policy**

#### **Step 1: Create a Persistent Volume (PV)**

Create a file (for example, `pv.yaml`) with the following content:

```yaml
apiVersion: v1                       # Kubernetes API version
kind: PersistentVolume              # Defines a PersistentVolume resource
metadata:
  name: example-pv                  # Unique name for the PV
spec:
  capacity:
    storage: 5Gi                    # Total storage provided (5 GiB)
  accessModes:
    - ReadWriteOnce                # Volume can be mounted as read-write by a single node at a time
  persistentVolumeReclaimPolicy: Retain  # Retain the volume and data even when the PVC is deleted
  hostPath:
    path: /mnt/data                # Uses a directory on the node (for demo purposes only)
```


> **Note:** When the `ReclaimPolicy` is set to `Retain`, the PersistentVolume (PV) and its data will **not be deleted** even if the associated PersistentVolumeClaim (PVC) is removed. This means the storage is **preserved for manual recovery or reassignment**, and must be manually handled by an administrator before it can be reused.


**Apply the PV:**

```bash
kubectl apply -f pv.yaml
```

**Verify the PV:**

```bash
kubectl get pv
kubectl describe pv example-pv
```

---

#### **Step 2: Create a Persistent Volume Claim (PVC)**

Create a file (for example, `pvc.yaml`) with the following content:

```yaml
apiVersion: v1                       # Kubernetes API version
kind: PersistentVolumeClaim         # Defines a PVC resource
metadata:
  name: example-pvc                 # Unique name for the PVC
spec:
  accessModes:
    - ReadWriteOnce                # Request volume to be mounted as read-write by a single node
  resources:
    requests:
      storage: 2Gi                 # Ask for at least 2Gi of storage (must be ≤ PV capacity)
```

> **Key Point:**  
> Since this PVC doesn’t explicitly specify a StorageClass, it will bind to a compatible PV if available. In this demo, the PV created above offers 5Gi, making it a suitable candidate for a 2Gi claim.

**Apply the PVC:**

```bash
kubectl apply -f pvc.yaml
```

**Verify the PVC status:**

```bash
kubectl get pvc
kubectl describe pvc example-pvc
```

---

#### **Step 3: Create a Pod That Uses the PVC**

Create a file (for example, `pod.yaml`) with the following content:

```yaml
apiVersion: v1                       # Kubernetes API version
kind: Pod                           # Defines a Pod resource
metadata:
  name: example-pod                 # Unique name for the Pod
spec:
  containers:
    - name: nginx-container         # Name of the container
      image: nginx                  # Container image to use
      volumeMounts:
        - mountPath: /usr/share/nginx/html  # Directory inside the container where the volume will be mounted
          name: persistent-storage  # Logical name for the volume mount
  volumes:
    - name: persistent-storage      # Volume's name referenced above
      persistentVolumeClaim:
        claimName: example-pvc      # Bind this volume to the previously created PVC
```

> **Important:**  
> When this Pod is created, Kubernetes will bind the PVC to the appropriate PV (if not already bound) and mount the volume. At this point, the PVC status should change from "Pending" to "Bound".

**Apply the Pod:**

```bash
kubectl apply -f pod.yaml
```

**Verify the Pod and its Volume Attachment:**

```bash
kubectl describe pod example-pod
```

---

#### **Final Verification**

After creating these resources, use the following commands to check that everything is in order:

- **Persistent Volumes:**
  ```bash
  kubectl get pv
  kubectl describe pv example-pv
  ```
- **Persistent Volume Claims:**
  ```bash
  kubectl get pvc
  kubectl describe pvc example-pvc
  ```
- **Pod Details:**
  ```bash
  kubectl describe pod example-pod
  ```

By following these steps, you’ll see that the PVC is bound to the PV and the Pod successfully mounts the storage. This demo illustrates how the `Retain` reclaim policy preserves data on the PV and how the dynamic binding between PVCs and PVs works within Kubernetes.

---