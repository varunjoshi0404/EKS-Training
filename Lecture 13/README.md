# Lecture 12: Kubernetes Probes

---

## **Transitioning from Self-Managed MySQL on EBS to Amazon RDS**

In our earlier deployment, we ran **MySQL with a single replica** backed by **Amazon EBS**. While this setup demonstrated persistence with Kubernetes volumes, it lacked **high availability (HA)**. With only one pod acting as a master, there were **no replicas for read scaling** or promotion in case of failure — a design that doesn’t hold up in production.

In traditional, on-premises Kubernetes environments, **StatefulSets** are often used to deploy databases.

> **StatefulSets** are a Kubernetes workload API object designed to manage stateful applications. They maintain stable network identities, persistent storage, and ordered, graceful deployment and scaling — which makes them a natural fit for databases.

However, even with StatefulSets, managing production-grade databases requires considerable expertise. You must account for:

* Backup strategies
* Rolling updates and patching
* HA and failover logic
* Replication (Master-Slave or Master-Master)
* Persistent volumes spanning multiple AZs (which EBS does not support)

Moreover, achieving **multi-AZ** availability with self-managed databases in Kubernetes is **difficult**, since EBS volumes and pods are tied to a specific Availability Zone (AZ).

---

## **Why Most Production Applications Use Managed Database Services**

In the public cloud, it's common practice to **offload the database layer to a managed service**, such as **Amazon RDS**, to reduce operational overhead.

Your typical application stack in Kubernetes might look like this:

| Tier                   | Platform / Service Example                                                                    |
| ---------------------- | --------------------------------------------------------------------------------------------- |
| Web Tier               | Deployed inside Kubernetes (e.g., frontend-flask using Flask/React)                           |
| Application Tier       | Deployed inside Kubernetes (e.g., REST APIs, backend processors)                              |
| Middleware             | Deployed in-cluster or managed (e.g., Kafka, RabbitMQ, NATS)                                  |
| Cache Tier             | **Amazon ElastiCache** (Redis or Memcached)                                                   |
| API Gateway            | **Amazon API Gateway**, **AWS App Mesh**, **AWS Load Balancer Controller**                    |
| **Relational DBs**     | **Amazon RDS** (MySQL, PostgreSQL, MariaDB, Oracle, SQL Server)                               |
| **Non-Relational DBs** | **Amazon DynamoDB**, **Amazon DocumentDB**, **Amazon Keyspaces**, **Neptune**, **Timestream** |


This separation of concerns allows teams to focus on **stateless components inside Kubernetes**, while leaving critical state management and availability guarantees to AWS-managed services.

---

## **What is Amazon RDS?**

**Amazon RDS (Relational Database Service)** is a managed database platform that makes it easy to set up, operate, and scale relational databases in the cloud. It supports engines like MySQL, PostgreSQL, MariaDB, Oracle, and Microsoft SQL Server.

Amazon RDS automates common tasks such as provisioning, patching, backup, recovery, and replication, so you can focus on application development instead of infrastructure management.

---

### **Key Benefits of Amazon RDS**

* **Automated Backups**: Daily snapshots and transaction log storage for point-in-time recovery.
* **High Availability**: Multi-AZ deployments for automatic failover and improved durability.
* **Read Replicas**: Offload read traffic and scale horizontally.
* **Automated Upgrades**: Patching and version upgrades with minimal downtime.
* **Monitoring & Logging**: Integrated with Amazon CloudWatch, Performance Insights, and enhanced logging for diagnostics.

---

Let me know if you'd like this wrapped as course slide content or formatted as markdown for inclusion in your LMS or GitHub repo.
