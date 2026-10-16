"""
ProductPulse — NLP Leakage-Safe Partitioner
Connected-component graph partitioning using product group (parent_asin) and canonical review hash.
Ensures zero data leakage across train, validation, and test splits.
Guarantees:
1. All reviews for a given parent_asin belong to the same split.
2. All duplicate reviews sharing a canonical_hash belong to the same split.
3. Connected components are never silently split to force exact split percentages.
"""
import hashlib
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from backend.app.nlp.schemas import PartitionAssignment, PartitionManifest


class ConnectedComponentPartitioner:
    """
    Partitions a collection of review records into train, validation, and test splits
    using a connected-component graph over (parent_asin, canonical_hash).
    """

    def __init__(
        self,
        train_target_pct: float = 0.70,
        val_target_pct: float = 0.15,
        test_target_pct: float = 0.15,
        seed: int = 42,
        salt: str = "productpulse_phase7a"
    ):
        if abs((train_target_pct + val_target_pct + test_target_pct) - 1.0) > 1e-6:
            raise ValueError("Split targets must sum to 1.0")
        self.train_target_pct = train_target_pct
        self.val_target_pct = val_target_pct
        self.test_target_pct = test_target_pct
        self.seed = seed
        self.salt = salt

    def build_partitions(
        self,
        records: List[Dict]
    ) -> Tuple[List[PartitionAssignment], PartitionManifest]:
        """
        Builds connected components and assigns entire components deterministically.
        
        Args:
            records: List of review dictionaries containing at minimum:
                     'review_id', 'parent_asin', 'canonical_hash', 'occurrence_index'.
                     
        Returns:
            Tuple of (List of PartitionAssignment, PartitionManifest).
        """
        # Step 1: Build adjacency between parent_asin and canonical_hash
        # Node namespaces: P:<parent_asin> and H:<canonical_hash>
        adj: Dict[str, Set[str]] = defaultdict(set)
        parent_asins: Set[str] = set()
        canonical_hashes: Set[str] = set()

        for r in records:
            p_node = f"P:{r['parent_asin']}"
            h_node = f"H:{r['canonical_hash']}"
            adj[p_node].add(h_node)
            adj[h_node].add(p_node)
            parent_asins.add(r['parent_asin'])
            canonical_hashes.add(r['canonical_hash'])

        # Step 2: Find connected components via BFS
        visited: Set[str] = set()
        components: List[Set[str]] = []

        all_nodes = sorted(list(adj.keys()))
        for node in all_nodes:
            if node not in visited:
                comp: Set[str] = set()
                queue = deque([node])
                visited.add(node)
                while queue:
                    curr = queue.popleft()
                    comp.add(curr)
                    for neighbor in sorted(list(adj[curr])):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)

        # Map each parent_asin and canonical_hash to a unique cluster_id
        # Cluster ID derived deterministically from the lexicographically smallest node
        node_to_cluster: Dict[str, str] = {}
        for idx, comp in enumerate(components):
            rep_node = sorted(list(comp))[0]
            cluster_id = f"cluster_{idx:05d}_{rep_node.replace(':', '_')}"
            for n in comp:
                node_to_cluster[n] = cluster_id

        # Step 3: Group records by cluster
        cluster_records: Dict[str, List[Dict]] = defaultdict(list)
        for r in records:
            p_node = f"P:{r['parent_asin']}"
            c_id = node_to_cluster[p_node]
            cluster_records[c_id].append(r)

        # Step 4: Deterministically assign clusters to splits using hash thresholding
        # We sort clusters by their deterministic hash to guarantee reproducibility
        cluster_assignments: Dict[str, str] = {}
        for c_id in sorted(list(cluster_records.keys())):
            hash_input = f"{self.seed}_{self.salt}_{c_id}".encode("utf-8")
            h_val = int(hashlib.sha256(hash_input).hexdigest(), 16)
            unit_norm = (h_val % 1000000) / 1000000.0

            if unit_norm < self.train_target_pct:
                split = "train"
            elif unit_norm < (self.train_target_pct + self.val_target_pct):
                split = "val"
            else:
                split = "test"
            cluster_assignments[c_id] = split

        # Step 5: Assign each review to its cluster's partition
        assignments: List[PartitionAssignment] = []
        train_count = 0
        val_count = 0
        test_count = 0
        duplicate_count = 0

        # Verification maps to check for leakage
        hash_to_split: Dict[str, str] = {}
        parent_to_split: Dict[str, str] = {}
        cross_partition_violations = 0

        for r in records:
            p_node = f"P:{r['parent_asin']}"
            c_id = node_to_cluster[p_node]
            split = cluster_assignments[c_id]

            if r.get('occurrence_index', 0) > 0:
                duplicate_count += 1

            # Leakage checks
            if r['canonical_hash'] in hash_to_split and hash_to_split[r['canonical_hash']] != split:
                cross_partition_violations += 1
            hash_to_split[r['canonical_hash']] = split

            if r['parent_asin'] in parent_to_split and parent_to_split[r['parent_asin']] != split:
                cross_partition_violations += 1
            parent_to_split[r['parent_asin']] = split

            if split == "train":
                train_count += 1
            elif split == "val":
                val_count += 1
            else:
                test_count += 1

            assignments.append(
                PartitionAssignment(
                    review_id=r['review_id'],
                    parent_asin=r['parent_asin'],
                    canonical_hash=r['canonical_hash'],
                    occurrence_index=r.get('occurrence_index', 0),
                    cluster_id=c_id,
                    partition=split
                )
            )

        total_revs = len(records)
        train_pct = round((train_count / total_revs) * 100, 2) if total_revs > 0 else 0.0
        val_pct = round((val_count / total_revs) * 100, 2) if total_revs > 0 else 0.0
        test_pct = round((test_count / total_revs) * 100, 2) if total_revs > 0 else 0.0

        # Cluster size distribution
        size_dist = {"1": 0, "2-5": 0, "6-20": 0, "21+": 0}
        for c_id, recs in cluster_records.items():
            sz = len(recs)
            if sz == 1:
                size_dist["1"] += 1
            elif 2 <= sz <= 5:
                size_dist["2-5"] += 1
            elif 6 <= sz <= 20:
                size_dist["6-20"] += 1
            else:
                size_dist["21+"] += 1

        manifest = PartitionManifest(
            random_seed=self.seed,
            salt=self.salt,
            total_reviews=total_revs,
            total_parent_asins=len(parent_asins),
            total_clusters=len(components),
            train_reviews=train_count,
            val_reviews=val_count,
            test_reviews=test_count,
            train_pct=train_pct,
            val_pct=val_pct,
            test_pct=test_pct,
            cluster_size_distribution=size_dist,
            duplicate_reviews_count=duplicate_count,
            duplicate_cross_partition_violations=cross_partition_violations,
            generated_at=datetime.now(timezone.utc).isoformat()
        )

        return assignments, manifest
