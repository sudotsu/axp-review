# Timestamp: 2025-10-27 04:40:38 UTC
# Hash: 505f7db691fb01d5fd8525ab3ed9226d794df0198af6054c6a6271c155f469cd
"""
AxProtocol Role Loader - Multi-Domain Support
Loads role definitions based on domain and build type
"""

import os
from pathlib import Path
from typing import Dict, Optional

def load_roles_by_pattern(build_type: str = "stable", domain: str = "strategy") -> Dict[str, Dict[str, str]]:
    """
    Load role definitions for a specific domain and build type.

    Args:
        build_type: "stable", "experimental", or "dev"
        domain: Domain name (marketing, ops, technical, creative, education, product, strategy, research)

    Returns:
        Dictionary with role names as keys and role config as values:
        {
            "strategist": {"name": "strategist", "content": "Role definition..."},
            "analyst": {"name": "analyst", "content": "Role definition..."},
            ...
        }

    Directory structure:
        roles/
        ├── marketing/
        │   ├── strategist_stable.txt
        │   ├── analyst_stable.txt
        │   └── ...
        ├── ops/
        │   └── ...
        └── technical/
            └── ...
    """

    # Determine base directory
    base_dir = Path(__file__).parent / "roles" / domain

    # Fallback to marketing if domain directory doesn't exist
    if not base_dir.exists():
        print(f"⚠️  Domain '{domain}' roles not found, falling back to 'marketing'")
        base_dir = Path(__file__).parent / "roles" / "marketing"

        # If marketing also doesn't exist, fall back to root roles
        if not base_dir.exists():
            base_dir = Path(__file__).parent / "roles"

    # Role names to load
    role_names = ["strategist", "analyst", "producer", "courier", "critic"]

    # Build suffix based on build type
    suffix = f"_{build_type}.txt"

    # Load each role
    roles = {}
    for role_name in role_names:
        role_path = base_dir / f"{role_name}{suffix}"

        # Try stable version if specified version doesn't exist
        if not role_path.exists() and build_type != "stable":
            role_path = base_dir / f"{role_name}_stable.txt"

        # Try without suffix
        if not role_path.exists():
            role_path = base_dir / f"{role_name}.txt"

        # Load role content
        if role_path.exists():
            with open(role_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            roles[role_name] = {
                "name": role_name,
                "content": content,
                "path": str(role_path),
                "domain": domain,
                "build_type": build_type
            }
        else:
            print(f"⚠️  Role file not found: {role_path}")
            # Provide fallback inline definition
            roles[role_name] = {
                "name": role_name,
                "content": _get_fallback_role(role_name, domain),
                "path": "inline_fallback",
                "domain": domain,
                "build_type": build_type
            }

    return roles


def _get_fallback_role(role_name: str, domain: str) -> str:
    """
    Get fallback role definition if file not found.

    Args:
        role_name: Name of the role
        domain: Domain context

    Returns:
        Role definition string
    """

    domain_contexts = {
        "marketing": "campaign assets and lead generation",
        "ops": "process documentation and workflow design",
        "technical": "system architecture and implementation",
        "creative": "original content and brand development",
        "education": "curriculum and learning materials",
        "product": "product specs and user stories",
        "strategy": "strategic plans and business analysis",
        "research": "research design and data analysis"
    }

    context = domain_contexts.get(domain, "deliverables")

    fallbacks = {
        "strategist": f"Role: Strategist. Define high-level strategy for {context}. Be decisive and ground all choices in the objective. Include clear success criteria.",

        "analyst": f"Role: Analyst. Validate assumptions and identify risks for {context}. Provide measurable metrics and A/B alternatives. Prioritize practical solutions.",

        "producer": f"Role: Producer. Create high-quality {context}. Focus on clarity, completeness, and professional execution. Include concrete deliverables.",

        "courier": f"Role: Courier. Design implementation plan for {context}. Include timeline, dependencies, and contingencies. Define clear handoffs.",

        "critic": f"Role: Critic. Audit {context} for quality, completeness, and alignment. Identify issues and provide specific fixes. Rate overall readiness."
    }

    return fallbacks.get(role_name, f"Role: {role_name.capitalize()}. Execute your responsibilities for {context}.")


def get_available_domains() -> list:
    """
    Get list of available domain directories.

    Returns:
        List of domain names that have role directories
    """
    roles_dir = Path(__file__).parent / "roles"

    if not roles_dir.exists():
        return ["marketing"]  # Default fallback

    domains = []
    for item in roles_dir.iterdir():
        if item.is_dir() and not item.name.startswith('_'):
            domains.append(item.name)

    return sorted(domains) if domains else ["marketing"]


def validate_roles(domain: str, build_type: str = "stable") -> bool:
    """
    Validate that all required roles exist for a domain.

    Args:
        domain: Domain name
        build_type: Build type

    Returns:
        True if all roles found, False otherwise
    """
    base_dir = Path(__file__).parent / "roles" / domain
    role_names = ["strategist", "analyst", "producer", "courier", "critic"]

    missing = []
    for role_name in role_names:
        role_path = base_dir / f"{role_name}_{build_type}.txt"
        if not role_path.exists():
            # Try stable fallback
            role_path = base_dir / f"{role_name}_stable.txt"
        if not role_path.exists():
            missing.append(role_name)

    if missing:
        print(f"⚠️  Missing roles for {domain}: {', '.join(missing)}")
        return False

    return True


if __name__ == "__main__":
    # Test the loader
    print("Testing Role Loader...")
    print("\nAvailable domains:", get_available_domains())

    # Test loading marketing roles
    print("\nLoading marketing roles...")
    roles = load_roles_by_pattern("stable", "marketing")
    for role_name, role_data in roles.items():
        print(f"  ✅ {role_name}: {len(role_data['content'])} chars")

    # Test validation
    print("\nValidating roles...")
    for domain in get_available_domains():
        valid = validate_roles(domain, "stable")
        status = "✅" if valid else "⚠️"
        print(f"  {status} {domain}")