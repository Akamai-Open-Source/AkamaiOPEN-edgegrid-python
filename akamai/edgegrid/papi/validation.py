"""Request validation functions for the PAPI client.

Each function mirrors the corresponding Go Validate() method from
AkamaiOPEN-edgegrid-golang/pkg/papi, enforcing identical field constraints,
required/empty/nil rules, enum checks, and nested validation logic.

Return type is ``str | None`` — an error message string when validation fails,
or ``None`` when the request is valid.
"""  # pylint: disable=too-many-lines

import re

from akamai.edgegrid.validation import parse_validation_errors
from akamai.edgegrid.papi import models

# ---------------------------------------------------------------------------
# Private constants
# ---------------------------------------------------------------------------

_VALID_RULE_FORMAT = re.compile(r"^(latest|v\d{4}-\d{2}-\d{2})$")
_MAX_HOSTNAMES_PER_PAGE = 999

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _validate_list(items, item_error_fn):
    """Validate each item in a list and return errors keyed by index."""
    if not items:
        return None
    errs = {}
    for idx, item in enumerate(items):
        item_errs = item_error_fn(item)
        if item_errs:
            errs[str(idx)] = item_errs
    return errs or None


def _unit_tested_field_check(record) -> str | None:
    """Mirror Go unitTestedFieldValidationRule.

    Only applies to *ComplianceRecordNone — if the compliance record is a
    ``ComplianceRecordNone`` and ``unit_tested`` is not ``True``, return an
    error message.  For any other type (including ``None``) return ``None``.
    """
    if not isinstance(record, models.ComplianceRecordNone):
        return None
    if not record.unit_tested:
        return (
            "for PRODUCTION activation network and nonComplianceRecord, "
            "UnitTested value has to be set to true, otherwise API will "
            "not work correctly"
        )
    return None


# -- Nested error collectors ------------------------------------------------
# These return ``dict | None`` so callers can embed them as nested error maps
# inside ``parse_validation_errors``.


def _property_clone_from_errors(clone) -> dict | None:
    """Collect errors for PropertyCloneFrom (Go always returns nil)."""
    # Go validates PropertyID and Version with no rules — always passes.
    _ = clone


def _property_create_errors(prop) -> dict | None:
    """Collect errors for PropertyCreate."""
    errs: dict[str, str | dict | None] = {}
    if not prop.product_id:
        errs["ProductID"] = "cannot be blank"
    if not prop.property_name:
        errs["PropertyName"] = "cannot be blank"
    if prop.clone_from is not None:
        clone_errs = _property_clone_from_errors(  # pylint: disable=assignment-from-no-return
            prop.clone_from
        )
        if clone_errs:
            errs["CloneFrom"] = clone_errs
    return {k: v for k, v in errs.items() if v is not None} or None


def _property_version_create_errors(version) -> dict | None:
    """Collect errors for PropertyVersionCreate."""
    errs: dict[str, str | None] = {}
    if not version.create_from_version:
        errs["CreateFromVersion"] = "cannot be blank"
    return {k: v for k, v in errs.items() if v is not None} or None


def _create_cp_code_errors(cpcode) -> dict | None:
    """Collect errors for CreateCPCode."""
    errs: dict[str, str | None] = {}
    if not cpcode.product_id:
        errs["ProductID"] = "cannot be blank"
    if not cpcode.cp_code_name:
        errs["CPCodeName"] = "cannot be blank"
    return {k: v for k, v in errs.items() if v is not None} or None


def _cp_code_contract_errors(contract) -> dict | None:
    """Collect errors for CPCodeContract."""
    errs: dict[str, str | None] = {}
    if not contract.contract_id:
        errs["ContractID"] = "cannot be blank"
    return {k: v for k, v in errs.items() if v is not None} or None


def _cp_code_product_errors(product) -> dict | None:
    """Collect errors for CPCodeProduct."""
    errs: dict[str, str | None] = {}
    if not product.product_id:
        errs["ProductID"] = "cannot be blank"
    return {k: v for k, v in errs.items() if v is not None} or None


def _cp_code_time_zone_errors(timezone) -> dict | None:
    """Collect errors for CPCodeTimeZone."""
    errs: dict[str, str | None] = {}
    if not timezone.time_zone_id:
        errs["TimeZoneID"] = "cannot be blank"
    return {k: v for k, v in errs.items() if v is not None} or None


def _use_case_errors(use_case) -> dict | None:
    """Collect errors for UseCase."""
    errs: dict[str, str | None] = {}
    if not use_case.option:
        errs["Option"] = "cannot be blank"
    if not use_case.type:
        errs["Type"] = "cannot be blank"
    elif use_case.type not in (models.UseCaseGlobal,):
        errs["Type"] = "must be a valid value"
    if not use_case.use_case:
        errs["UseCase"] = "cannot be blank"
    return {k: v for k, v in errs.items() if v is not None} or None


def _edge_hostname_create_errors(eh) -> dict | None:
    """Collect errors for EdgeHostnameCreate."""
    errs: dict[str, str | dict | None] = {}

    if not eh.domain_prefix:
        errs["DomainPrefix"] = "cannot be blank"

    # DomainSuffix: Required + conditional domain suffix validation
    if not eh.domain_suffix:
        errs["DomainSuffix"] = "cannot be blank"
    else:
        secure = getattr(eh, "secure_network", "")
        if secure == models.EHSecureNetworkStandardTLS and eh.domain_suffix != "edgesuite.net":
            errs["DomainSuffix"] = "must be a valid value"
        elif secure == models.EHSecureNetworkSharedCert and eh.domain_suffix != "akamaized.net":
            errs["DomainSuffix"] = "must be a valid value"
        elif secure == models.EHSecureNetworkEnhancedTLS and eh.domain_suffix != "edgekey.net":
            errs["DomainSuffix"] = "must be a valid value"

    if not eh.product_id:
        errs["ProductID"] = "cannot be blank"

    # CertEnrollmentID required only when SecureNetwork == EnhancedTLS
    secure = getattr(eh, "secure_network", "")
    if secure == models.EHSecureNetworkEnhancedTLS and not eh.cert_enrollment_id:
        errs["CertEnrollmentID"] = "cannot be blank"

    # IPVersionBehavior: Required + In
    if not eh.ip_version_behavior:
        errs["IPVersionBehavior"] = "cannot be blank"
    elif eh.ip_version_behavior not in (
        models.EHIPVersionV4,
        models.EHIPVersionV6Performance,
        models.EHIPVersionV6Compliance,
    ):
        errs["IPVersionBehavior"] = "must be a valid value"

    # SecureNetwork: In (optional, validated only when non-empty)
    if secure and secure not in (
        models.EHSecureNetworkStandardTLS,
        models.EHSecureNetworkSharedCert,
        models.EHSecureNetworkEnhancedTLS,
    ):
        errs["SecureNetwork"] = "must be a valid value"

    # UseCases nested validation
    uc_errs = _validate_list(getattr(eh, "use_cases", None), _use_case_errors)
    if uc_errs:
        errs["UseCases"] = uc_errs

    return {k: v for k, v in errs.items() if v is not None} or None


def _mtls_errors(mtls_obj) -> dict | None:
    """Collect errors for MTLS."""
    errs: dict[str, str | None] = {}
    if not mtls_obj.ca_set_id:
        errs["CASetID"] = "cannot be blank"
    elif not mtls_obj.ca_set_id.isdigit():
        errs["CASetID"] = "must contain digits only"
    return {k: v for k, v in errs.items() if v is not None} or None


def _ccm_certificates_errors(certs) -> dict | None:
    """Collect errors for CCMCertificates."""
    errs: dict[str, str | None] = {}
    if certs.rsa_cert_id and not certs.rsa_cert_id.isdigit():
        errs["RSACertID"] = "must contain digits only"
    if certs.ecdsa_cert_id and not certs.ecdsa_cert_id.isdigit():
        errs["ECDSACertID"] = "must contain digits only"
    return {k: v for k, v in errs.items() if v is not None} or None


def _ccm_hostname_error(  # pylint: disable=too-many-return-statements
    cert_type, certs, mtls_obj, tls_config,
) -> str | None:
    """Mirror Go validateCCMHostname helper.

    Returns an error string describing the first CCM configuration issue
    found, or ``None`` if valid.
    """
    cert_type_str = str(cert_type) if cert_type else ""
    _not_ccm_msg = (
        "should not be provided when certProvisioningType is not CCM"
    )

    if cert_type_str != models.CertTypeCCM:
        # Not CCM — reject related fields if present
        if certs is not None:
            return f"CCM certificate details {_not_ccm_msg}"
        if mtls_obj is not None:
            return f"mTLS details {_not_ccm_msg}"
        if tls_config is not None:
            return f"TLS configuration {_not_ccm_msg}"
        return None

    # cert_type IS CCM
    if certs is None:
        return (
            "must contain ccmCertificates when "
            "certProvisioningType is CCM"
        )

    rsa = getattr(certs, "rsa_cert_id", "")
    ecdsa = getattr(certs, "ecdsa_cert_id", "")
    if not rsa and not ecdsa:
        return "either RSACertID or ECDSACertID must be provided"

    if tls_config is not None:
        cipher = getattr(tls_config, "cipher_profile", "")
        if not cipher:
            return (
                "cipher profile must not be empty when "
                "TLS configuration is provided"
            )

    return None


def _hostname_errors(hostname) -> dict | None:
    """Collect errors for Hostname."""
    errs: dict[str, str | dict | None] = {}

    # MTLS nested validation (only when non-nil)
    if getattr(hostname, "mtls", None) is not None:
        m_errs = _mtls_errors(hostname.mtls)
        if m_errs:
            errs["MTLS"] = m_errs

    # CCMCertificates nested validation (only when non-nil)
    if getattr(hostname, "ccm_certificates", None) is not None:
        c_errs = _ccm_certificates_errors(hostname.ccm_certificates)
        if c_errs:
            errs["CCMCertificates"] = c_errs

    # validateCCMHostname
    ccm_err = _ccm_hostname_error(
        getattr(hostname, "cert_provisioning_type", ""),
        getattr(hostname, "ccm_certificates", None),
        getattr(hostname, "mtls", None),
        getattr(hostname, "tls_configuration", None),
    )
    if ccm_err:
        errs["ValidateCCMHostname"] = ccm_err

    # DomainOwnershipVerification must be nil (response-only field)
    if getattr(hostname, "domain_ownership_verification", None) is not None:
        errs["DomainOwnershipVerification"] = (
            "field is returned only in responses and should not be "
            "populated in requests"
        )

    return {k: v for k, v in errs.items() if v is not None} or None


def _hostname_add_errors(hostname) -> dict | None:
    """Collect errors for HostnameAdd."""
    errs: dict[str, str | dict | None] = {}

    if not hostname.cname_from:
        errs["CnameFrom"] = "cannot be blank"

    # CnameType: When(non-empty, HostnameCnameType.Validate())
    cname_type = getattr(hostname, "cname_type", "")
    if cname_type:
        ct_err = validate_hostname_cname_type(cname_type)
        if ct_err:
            errs["CnameType"] = ct_err

    # CertProvisioningType: When(non-empty, CertType.Validate())
    cert_type = getattr(hostname, "cert_provisioning_type", "")
    if cert_type:
        cpt_err = validate_cert_type(cert_type)
        if cpt_err:
            errs["CertProvisioningType"] = cpt_err

    # MTLS nested (only when non-nil)
    if getattr(hostname, "mtls", None) is not None:
        m_errs = _mtls_errors(hostname.mtls)
        if m_errs:
            errs["MTLS"] = m_errs

    # CCMCertificates nested (only when non-nil)
    if getattr(hostname, "ccm_certificates", None) is not None:
        c_errs = _ccm_certificates_errors(hostname.ccm_certificates)
        if c_errs:
            errs["CCMCertificates"] = c_errs

    # validateCCMHostname
    ccm_err = _ccm_hostname_error(
        cert_type,
        getattr(hostname, "ccm_certificates", None),
        getattr(hostname, "mtls", None),
        getattr(hostname, "tls_configuration", None),
    )
    if ccm_err:
        errs["ValidateCCMHostname"] = ccm_err

    # Custom rule: either CnameTo or EdgeHostnameID must be provided
    cname_to = getattr(hostname, "cname_to", "")
    edge_hostname_id = getattr(hostname, "edge_hostname_id", "")
    if not cname_to and not edge_hostname_id:
        errs["required parameters"] = (
            "either CnameTo or EdgeHostnameID must be provided"
        )

    return {k: v for k, v in errs.items() if v is not None} or None


def _compliance_record_none_errors(record) -> dict | None:
    """Collect errors for ComplianceRecordNone."""
    errs: dict[str, str | None] = {}
    if not record.customer_email:
        errs["CustomerEmail"] = "cannot be blank"
    if not record.peer_reviewed_by:
        errs["PeerReviewedBy"] = "cannot be blank"
    return {k: v for k, v in errs.items() if v is not None} or None


def _compliance_record_other_errors(record) -> dict | None:
    """Collect errors for ComplianceRecordOther."""
    errs: dict[str, str | None] = {}
    if not record.other_noncompliance_reason:
        errs["OtherNoncomplianceReason"] = "cannot be blank"
    return {k: v for k, v in errs.items() if v is not None} or None


def _rule_variable_errors(variable) -> dict | None:
    """Collect errors for RuleVariable."""
    errs: dict[str, str | None] = {}
    if not variable.name:
        errs["Name"] = "cannot be blank"
    if getattr(variable, "value", None) is None:
        errs["Value"] = "is required"
    return {k: v for k, v in errs.items() if v is not None} or None


def _rule_custom_override_errors(override) -> dict | None:
    """Collect errors for RuleCustomOverride."""
    errs: dict[str, str | None] = {}
    if not override.name:
        errs["Name"] = "cannot be blank"
    if not override.override_id:
        errs["OverrideID"] = "cannot be blank"
    return {k: v for k, v in errs.items() if v is not None} or None


def _rule_behavior_errors(behavior) -> dict | None:
    """Collect errors for RuleBehavior.

    Go validates Name and Options with no explicit rules — for basic types
    this always passes.  Only returns errors if the nested objects themselves
    implement Validatable (they don't for RuleBehavior fields).
    """
    # Go: validation.Validate(b.Name) — no rules, always passes for string
    # Go: validation.Validate(b.Options) — RuleOptions is a map, no Validate()
    _ = behavior


def _rules_errors(rules) -> dict | None:
    """Collect errors for Rules (recursive via Children)."""
    errs: dict[str, str | dict | None] = {}

    # Behaviors: validate each
    behaviors = getattr(rules, "behaviors", None)
    if behaviors:
        beh_errs = _validate_list(behaviors, _rule_behavior_errors)
        if beh_errs:
            errs["Behaviors"] = beh_errs

    # Name: Required
    if not rules.name:
        errs["Name"] = "cannot be blank"

    # CustomOverride: validate if non-nil
    custom_override = getattr(rules, "custom_override", None)
    if custom_override is not None:
        co_errs = _rule_custom_override_errors(custom_override)
        if co_errs:
            errs["CustomOverride"] = co_errs

    # Criteria: validate each (RuleBehavior used for criteria too in Go)
    criteria = getattr(rules, "criteria", None)
    if criteria:
        crit_errs = _validate_list(criteria, _rule_behavior_errors)
        if crit_errs:
            errs["Criteria"] = crit_errs

    # Children: validate each (recursive Rules)
    children = getattr(rules, "children", None)
    if children:
        child_errs = _validate_list(children, _rules_errors)
        if child_errs:
            errs["Children"] = child_errs

    # Variables: validate each
    variables = getattr(rules, "variables", None)
    if variables:
        var_errs = _validate_list(variables, _rule_variable_errors)
        if var_errs:
            errs["Variables"] = var_errs

    # Comments: validation.Validate(r.Comments) — string, no rules, always passes

    return {k: v for k, v in errs.items() if v is not None} or None


def _rules_update_errors(rules_update) -> dict | None:
    """Collect errors for RulesUpdate."""
    errs: dict[str, str | dict | None] = {}

    # Rules: nested
    rules_obj = getattr(rules_update, "rules", None)
    if rules_obj is not None:
        r_errs = _rules_errors(rules_obj)
        if r_errs:
            errs["Rules"] = r_errs

    # Comments: validation.Validate(ru.Comments) — always passes for string

    return {k: v for k, v in errs.items() if v is not None} or None


def _patch_property_hostname_bucket_add_errors(add) -> dict | None:
    """Collect errors for PatchPropertyHostnameBucketAdd."""
    errs: dict[str, str | None] = {}
    if not add.edge_hostname_id:
        errs["EdgeHostnameID"] = "cannot be blank"

    # CertProvisioningType: Required + CertType.Validate()
    cert_type = getattr(add, "cert_provisioning_type", "")
    if not cert_type:
        errs["CertProvisioningType"] = "cannot be blank"
    else:
        ct_err = validate_cert_type(cert_type)
        if ct_err:
            errs["CertProvisioningType"] = ct_err

    # CnameType: Required + HostnameCnameType.Validate()
    cname_type = getattr(add, "cname_type", "")
    if not cname_type:
        errs["CnameType"] = "cannot be blank"
    else:
        cnt_err = validate_hostname_cname_type(cname_type)
        if cnt_err:
            errs["CnameType"] = cnt_err

    if not add.cname_from:
        errs["CnameFrom"] = "cannot be blank"

    return {k: v for k, v in errs.items() if v is not None} or None


# =========================================================================
# Exported enum / type validators
# =========================================================================


def validate_activation_network(network: str) -> str | None:
    """Validate ActivationNetwork value.

    Mirrors Go ActivationNetwork.Validate().
    Returns ``None`` for empty values (In rule skips empty).
    """
    if not network:
        return None
    if network not in (
        models.ActivationNetworkStaging,
        models.ActivationNetworkProduction,
    ):
        return (
            f"value '{network}' is invalid. Must be one of: "
            f"'{models.ActivationNetworkStaging}' or "
            f"'{models.ActivationNetworkProduction}'"
        )
    return None


def validate_sort_order(sort: str) -> str | None:
    """Validate SortOrder value.

    Mirrors Go SortOrder.Validate().
    """
    if not sort:
        return None
    if sort not in (models.SortAscending, models.SortDescending):
        return (
            f"value '{sort}' is invalid. Must be one of: "
            f"'{models.SortAscending}' or '{models.SortDescending}'"
        )
    return None


def validate_cert_type(cert_type: str) -> str | None:
    """Validate CertType value.

    Mirrors Go CertType.Validate().
    """
    if not cert_type:
        return None
    if cert_type not in (
        models.CertTypeCPSManaged,
        models.CertTypeDefault,
        models.CertTypeCCM,
    ):
        return (
            f"value '{cert_type}' is invalid. Must be one of: "
            f"'{models.CertTypeCPSManaged}', "
            f"'{models.CertTypeDefault}' or "
            f"'{models.CertTypeCCM}'"
        )
    return None


def validate_hostname_cname_type(cname_type: str) -> str | None:
    """Validate HostnameCnameType value.

    Mirrors Go HostnameCnameType.Validate().
    """
    if not cname_type:
        return None
    if cname_type not in (models.HostnameCnameTypeEdgeHostname,):
        return (
            f"value '{cname_type}' is invalid. "
            f"There is only one supported value of: "
            f"{models.HostnameCnameTypeEdgeHostname}"
        )
    return None


# =========================================================================
# Exported nested-type validators
# =========================================================================


def validate_property_create(prop) -> str | None:
    """Validate PropertyCreate. Mirrors Go PropertyCreate.Validate()."""
    errs = _property_create_errors(prop)
    return parse_validation_errors(errs) if errs else None


def validate_property_clone_from(clone) -> str | None:
    """Validate PropertyCloneFrom. Mirrors Go PropertyCloneFrom.Validate()."""
    # Go's PropertyCloneFrom.Validate() always returns nil.
    _ = clone


def validate_property_version_create(version) -> str | None:
    """Validate PropertyVersionCreate. Mirrors Go PropertyVersionCreate.Validate()."""
    errs = _property_version_create_errors(version)
    return parse_validation_errors(errs) if errs else None


def validate_edge_hostname_create(eh) -> str | None:
    """Validate EdgeHostnameCreate. Mirrors Go EdgeHostnameCreate.Validate()."""
    errs = _edge_hostname_create_errors(eh)
    return parse_validation_errors(errs) if errs else None


def validate_use_case(use_case) -> str | None:
    """Validate UseCase. Mirrors Go UseCase.Validate()."""
    errs = _use_case_errors(use_case)
    return parse_validation_errors(errs) if errs else None


def validate_domain_prefix(prefix: str, suffix: str) -> str | None:
    """Validate edge hostname domain prefix against suffix patterns.

    Mirrors Go domain prefix validation in edgehostname.go.
    """
    if not prefix:
        return "cannot be blank"
    if suffix == "akamaized.net":
        if not re.match(models.AkamaizedNetDomainRegexPattern, prefix):
            return "must be in a valid format"
    elif suffix in ("edgesuite.net", "edgekey.net"):
        if not re.match(models.DefaultEHDomainRegexPattern, prefix):
            return "must be in a valid format"
    return None


def validate_compliance_record_none(record) -> str | None:
    """Validate ComplianceRecordNone. Mirrors Go ComplianceRecordNone.Validate()."""
    errs = _compliance_record_none_errors(record)
    return parse_validation_errors(errs) if errs else None


def validate_compliance_record_other(record) -> str | None:
    """Validate ComplianceRecordOther. Mirrors Go ComplianceRecordOther.Validate()."""
    errs = _compliance_record_other_errors(record)
    return parse_validation_errors(errs) if errs else None


def validate_hostname(hostname) -> str | None:
    """Validate Hostname. Mirrors Go Hostname.Validate()."""
    errs = _hostname_errors(hostname)
    return parse_validation_errors(errs) if errs else None


def validate_mtls(mtls_obj) -> str | None:
    """Validate MTLS. Mirrors Go MTLS.Validate()."""
    errs = _mtls_errors(mtls_obj)
    return parse_validation_errors(errs) if errs else None


def validate_ccm_certificates(certs) -> str | None:
    """Validate CCMCertificates. Mirrors Go CCMCertificates.Validate()."""
    errs = _ccm_certificates_errors(certs)
    return parse_validation_errors(errs) if errs else None


def validate_ccm_hostname(cert_type, certs, mtls_obj, tls_config) -> str | None:
    """Validate CCM hostname configuration.

    Mirrors Go validateCCMHostname helper.
    """
    return _ccm_hostname_error(cert_type, certs, mtls_obj, tls_config)


def validate_hostname_add(hostname) -> str | None:
    """Validate HostnameAdd. Mirrors Go HostnameAdd.Validate()."""
    errs = _hostname_add_errors(hostname)
    return parse_validation_errors(errs) if errs else None


def validate_rules_update(rules_update) -> str | None:
    """Validate RulesUpdate. Mirrors Go RulesUpdate.Validate()."""
    errs = _rules_update_errors(rules_update)
    return parse_validation_errors(errs) if errs else None


def validate_rules(rules) -> str | None:
    """Validate Rules. Mirrors Go Rules.Validate()."""
    errs = _rules_errors(rules)
    return parse_validation_errors(errs) if errs else None


def validate_rule_behavior(behavior) -> str | None:
    """Validate RuleBehavior. Mirrors Go RuleBehavior.Validate()."""
    # Go's RuleBehavior.Validate() always returns nil.
    _ = behavior


def validate_rule_custom_override(override) -> str | None:
    """Validate RuleCustomOverride. Mirrors Go RuleCustomOverride.Validate()."""
    errs = _rule_custom_override_errors(override)
    return parse_validation_errors(errs) if errs else None


def validate_rule_variable(variable) -> str | None:
    """Validate RuleVariable. Mirrors Go RuleVariable.Validate()."""
    errs = _rule_variable_errors(variable)
    return parse_validation_errors(errs) if errs else None


def validate_cp_code_contract(contract) -> str | None:
    """Validate CPCodeContract. Mirrors Go CPCodeContract.Validate()."""
    errs = _cp_code_contract_errors(contract)
    return parse_validation_errors(errs) if errs else None


def validate_cp_code_product(product) -> str | None:
    """Validate CPCodeProduct. Mirrors Go CPCodeProduct.Validate()."""
    errs = _cp_code_product_errors(product)
    return parse_validation_errors(errs) if errs else None


def validate_cp_code_time_zone(timezone) -> str | None:
    """Validate CPCodeTimeZone. Mirrors Go CPCodeTimeZone.Validate()."""
    errs = _cp_code_time_zone_errors(timezone)
    return parse_validation_errors(errs) if errs else None


def validate_create_cp_code(cpcode) -> str | None:
    """Validate CreateCPCode. Mirrors Go CreateCPCode.Validate()."""
    errs = _create_cp_code_errors(cpcode)
    return parse_validation_errors(errs) if errs else None


def validate_patch_property_hostname_bucket_body(body) -> str | None:
    """Validate PatchPropertyHostnameBucketBody.

    Mirrors Go PatchPropertyHostnameBucketBody.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    # Network: Required + Network.Validate()
    if not body.network:
        errs["Network"] = "cannot be blank"
    else:
        net_err = validate_activation_network(body.network)
        if net_err:
            errs["Network"] = net_err

    # Add: nested validation of each item
    add_errs = _validate_list(
        getattr(body, "add", None), _patch_property_hostname_bucket_add_errors
    )
    if add_errs:
        errs["Add"] = add_errs

    # Custom: at least one hostname in add or remove
    add_list = getattr(body, "add", None) or []
    remove_list = getattr(body, "remove", None) or []
    if not add_list and not remove_list:
        errs[""] = "at least one hostname is required in add or remove list"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_patch_property_hostname_bucket_add(add) -> str | None:
    """Validate PatchPropertyHostnameBucketAdd.

    Mirrors Go PatchPropertyHostnameBucketAdd.Validate().
    """
    errs = _patch_property_hostname_bucket_add_errors(add)
    return parse_validation_errors(errs) if errs else None


def validate_patch_property_version_hostnames_request_body(body) -> str | None:
    """Validate PatchPropertyVersionHostnamesRequestBody.

    Mirrors Go PatchPropertyVersionHostnamesRequestBody.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    # Add: nested validation of each HostnameAdd
    add_list = getattr(body, "add", None)
    if add_list:
        add_errs = _validate_list(add_list, _hostname_add_errors)
        if add_errs:
            errs["Add"] = add_errs

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — activation.go
# =========================================================================


def validate_create_activation_request(req) -> str | None:  # pylint: disable=too-many-branches
    """Validate CreateActivationRequest.

    Mirrors Go CreateActivationRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"

    activation = getattr(req, "activation", None)
    if activation is not None:
        if activation.account_id:
            errs["Activation.AccountID"] = "must be blank"
        if activation.activation_id:
            errs["Activation.ActivationID"] = "must be blank"
        if getattr(activation, "fallback_info", None) is not None:
            errs["Activation.FallbackInfo"] = "must be blank"
        if getattr(activation, "fma_activation_state", ""):
            errs["Activation.FMAActivationState"] = "must be blank"
        if activation.group_id:
            errs["Activation.GroupID"] = "must be blank"

        # Network: Network.Validate() (In rule — skips empty)
        net_err = validate_activation_network(
            getattr(activation, "network", "")
        )
        if net_err:
            errs["Activation.Network"] = net_err

        # NotifyEmails: Length(1, 0)
        ne = getattr(activation, "notify_emails", None)
        if ne is not None and len(ne) < 1:
            errs["Activation.NotifyEmails"] = (
                "the length must be no less than 1"
            )

        if getattr(activation, "property_id", ""):
            errs["Activation.PropertyID"] = "must be blank"
        if getattr(activation, "property_name", ""):
            errs["Activation.PropertyName"] = "must be blank"
        if getattr(activation, "status", ""):
            errs["Activation.Status"] = "must be blank"
        if getattr(activation, "submit_date", ""):
            errs["Activation.SubmitDate"] = "must be blank"
        if getattr(activation, "update_date", ""):
            errs["Activation.UpdateDate"] = "must be blank"

        # Type: In(Activate, Deactivate) — skips empty
        act_type = getattr(activation, "activation_type", "")
        if act_type and act_type not in (
            models.ActivationTypeActivate,
            models.ActivationTypeDeactivate,
        ):
            errs["Activation.Type"] = "must be a valid value"

        # ComplianceRecord: When(PRODUCTION, unitTestedFieldValidationRule)
        if (
            getattr(activation, "network", "")
            == models.ActivationNetworkProduction
        ):
            record = getattr(activation, "compliance_record", None)
            cr_err = _unit_tested_field_check(record)
            if cr_err:
                errs["Activation.ComplianceRecord"] = cr_err

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_activations_request(req) -> str | None:
    """Validate GetActivationsRequest. Mirrors Go GetActivationsRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_activation_request(req) -> str | None:
    """Validate GetActivationRequest. Mirrors Go GetActivationRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    if not req.activation_id:
        errs["ActivationID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_cancel_activation_request(req) -> str | None:
    """Validate CancelActivationRequest. Mirrors Go CancelActivationRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    if not req.activation_id:
        errs["ActivationID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — active_property_hostname.go
# =========================================================================


def validate_list_active_property_hostnames_request(req) -> str | None:
    """Validate ListActivePropertyHostnamesRequest.

    Mirrors Go ListActivePropertyHostnamesRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"

    net = getattr(req, "network", "")
    net_err = validate_activation_network(net)
    if net_err:
        errs["Network"] = net_err

    sort = getattr(req, "sort", "")
    sort_err = validate_sort_order(sort)
    if sort_err:
        errs["Sort"] = sort_err

    offset = getattr(req, "offset", 0)
    if offset != 0 and offset < 0:
        errs["Offset"] = "must be no less than 0"

    limit = getattr(req, "limit", 0)
    if limit != 0:
        if limit < 1:
            errs["Limit"] = "must be no less than 1"
        elif limit > _MAX_HOSTNAMES_PER_PAGE:
            errs["Limit"] = f"must be no greater than {_MAX_HOSTNAMES_PER_PAGE}"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_active_property_hostnames_diff_request(req) -> str | None:
    """Validate GetActivePropertyHostnamesDiffRequest.

    Mirrors Go GetActivePropertyHostnamesDiffRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"

    offset = getattr(req, "offset", 0)
    if offset != 0 and offset < 0:
        errs["Offset"] = "must be no less than 0"

    limit = getattr(req, "limit", 0)
    if limit != 0:
        if limit < 1:
            errs["Limit"] = "must be no less than 1"
        elif limit > _MAX_HOSTNAMES_PER_PAGE:
            errs["Limit"] = f"must be no greater than {_MAX_HOSTNAMES_PER_PAGE}"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_list_active_account_hostnames_request(req) -> str | None:
    """Validate ListActiveAccountHostnamesRequest.

    Mirrors Go ListActiveAccountHostnamesRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    net = getattr(req, "network", "")
    net_err = validate_activation_network(net)
    if net_err:
        errs["Network"] = net_err

    sort = getattr(req, "sort", "")
    sort_err = validate_sort_order(sort)
    if sort_err:
        errs["Sort"] = sort_err

    offset = getattr(req, "offset", 0)
    if offset != 0 and offset < 0:
        errs["Offset"] = "must be no less than 0"

    limit = getattr(req, "limit", 0)
    if limit != 0:
        if limit < 1:
            errs["Limit"] = "must be no less than 1"
        elif limit > _MAX_HOSTNAMES_PER_PAGE:
            errs["Limit"] = f"must be no greater than {_MAX_HOSTNAMES_PER_PAGE}"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — cpcode.go
# =========================================================================


def validate_get_cp_codes_request(req) -> str | None:
    """Validate GetCPCodesRequest. Mirrors Go GetCPCodesRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_cp_code_request(req) -> str | None:
    """Validate GetCPCodeRequest. Mirrors Go GetCPCodeRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    if not req.cpcode_id:
        errs["CPCodeID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_create_cp_code_request(req) -> str | None:
    """Validate CreateCPCodeRequest. Mirrors Go CreateCPCodeRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    cpcode = getattr(req, "cpcode", None)
    if cpcode is None:
        errs["CPCode"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_update_cp_code_request(req) -> str | None:
    """Validate UpdateCPCodeRequest. Mirrors Go UpdateCPCodeRequest.Validate()."""
    errs: dict[str, str | dict | None] = {}
    if not getattr(req, "id", 0):
        errs["ID"] = "cannot be blank"
    if not getattr(req, "name", ""):
        errs["Name"] = "cannot be blank"
    contracts = getattr(req, "contracts", None)
    if not contracts:
        errs["Contracts"] = "cannot be blank"
    products = getattr(req, "products", None)
    if not products:
        errs["Products"] = "cannot be blank"
    # OverrideTimeZone: Validate() triggers nested validation (no explicit rules)
    override_tz = getattr(req, "override_time_zone", None)
    if override_tz is not None:
        tz_errs = _cp_code_time_zone_errors(override_tz)
        if tz_errs:
            errs["OverrideTimeZone"] = tz_errs
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — domain_ownership_validation.go
# =========================================================================


def validate_validate_domains_ownership_request(req) -> str | None:
    """Validate ValidateDomainsOwnershipRequest.

    Mirrors Go ValidateDomainsOwnershipRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    # Go validates r.Body.Hostnames — access via body attr
    body = getattr(req, "body", None)
    hostnames = getattr(body, "hostnames", None) if body else None

    if not hostnames:
        errs["Hostnames"] = "cannot be blank"
    else:
        each_errs: dict[str, str] = {}
        for i, hostname in enumerate(hostnames):
            if not hostname:
                each_errs[str(i)] = "cannot be blank"
        if each_errs:
            errs["Hostnames"] = each_errs

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — edgehostname.go
# =========================================================================


def validate_get_edge_hostnames_request(req) -> str | None:
    """Validate GetEdgeHostnamesRequest. Mirrors Go GetEdgeHostnamesRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_edge_hostname_request(req) -> str | None:
    """Validate GetEdgeHostnameRequest. Mirrors Go GetEdgeHostnameRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.edge_hostname_id:
        errs["EdgeHostnameID"] = "cannot be blank"
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_create_edge_hostname_request(req) -> str | None:
    """Validate CreateEdgeHostnameRequest.

    Mirrors Go CreateEdgeHostnameRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"

    # EdgeHostname: nested validation (Validatable interface)
    eh = getattr(req, "edge_hostname", None)
    if eh is not None:
        eh_errs = _edge_hostname_create_errors(eh)
        if eh_errs:
            errs["EdgeHostname"] = eh_errs

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — include.go
# =========================================================================


def validate_list_includes_request(req) -> str | None:
    """Validate ListIncludesRequest. Mirrors Go ListIncludesRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_list_include_parents_request(req) -> str | None:
    """Validate ListIncludeParentsRequest. Mirrors Go ListIncludeParentsRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_include_request(req) -> str | None:
    """Validate GetIncludeRequest. Mirrors Go GetIncludeRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_create_include_request(req) -> str | None:
    """Validate CreateIncludeRequest.

    Mirrors Go CreateIncludeRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    if not req.include_name:
        errs["IncludeName"] = "cannot be blank"

    include_type = getattr(req, "include_type", "")
    if not include_type:
        errs["IncludeType"] = "cannot be blank"
    elif include_type not in (
        models.IncludeTypeMicroServices,
        models.IncludeTypeCommonSettings,
    ):
        errs["IncludeType"] = "must be a valid value"

    if not req.product_id:
        errs["ProductID"] = "cannot be blank"

    # CloneIncludeFrom: When(not nil, validateCloneIncludeID / validateCloneVersion)
    clone = getattr(req, "clone_include_from", None)
    if clone is not None:
        clone_id = getattr(clone, "include_id", "")
        if not clone_id:
            errs["CloneIncludeFrom.IncludeID"] = "cannot be blank"
        clone_ver = getattr(clone, "version", 0)
        if not clone_ver:
            errs["CloneIncludeFrom.Version"] = "cannot be blank"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_delete_include_request(req) -> str | None:
    """Validate DeleteIncludeRequest. Mirrors Go DeleteIncludeRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — include_activations.go
# =========================================================================


def validate_activate_include_request(req) -> str | None:
    """Validate ActivateIncludeRequest.

    Mirrors Go ActivateIncludeRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    if not getattr(req, "version", 0):
        errs["Version"] = "cannot be blank"
    if not getattr(req, "network", ""):
        errs["Network"] = "cannot be blank"
    notify = getattr(req, "notify_emails", None)
    if not notify:
        errs["NotifyEmails"] = "cannot be blank"

    # ComplianceRecord: When(PRODUCTION, unitTestedFieldValidationRule)
    if getattr(req, "network", "") == models.ActivationNetworkProduction:
        record = getattr(req, "compliance_record", None)
        cr_err = _unit_tested_field_check(record)
        if cr_err:
            errs["ComplianceRecord"] = cr_err

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_deactivate_include_request(req) -> str | None:
    """Validate DeactivateIncludeRequest.

    Mirrors Go DeactivateIncludeRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    if not getattr(req, "version", 0):
        errs["Version"] = "cannot be blank"
    if not getattr(req, "network", ""):
        errs["Network"] = "cannot be blank"
    notify = getattr(req, "notify_emails", None)
    if not notify:
        errs["NotifyEmails"] = "cannot be blank"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_include_activation_request(req) -> str | None:
    """Validate GetIncludeActivationRequest.

    Mirrors Go GetIncludeActivationRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    if not req.activation_id:
        errs["ActivationID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_cancel_include_activation_request(req) -> str | None:
    """Validate CancelIncludeActivationRequest.

    Mirrors Go CancelIncludeActivationRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    if not req.activation_id:
        errs["ActivationID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_list_include_activations_request(req) -> str | None:
    """Validate ListIncludeActivationsRequest.

    Mirrors Go ListIncludeActivationsRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — include_rule.go
# =========================================================================


def validate_get_include_rule_tree_request(req) -> str | None:
    """Validate GetIncludeRuleTreeRequest.

    Mirrors Go GetIncludeRuleTreeRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    if not getattr(req, "include_version", 0):
        errs["IncludeVersion"] = "cannot be blank"

    # RuleFormat: Match(validRuleFormat) — skips empty
    rule_format = getattr(req, "rule_format", "")
    if rule_format and not _VALID_RULE_FORMAT.match(rule_format):
        errs["RuleFormat"] = "must be in a valid format"

    # ValidateMode: In(Fast, Full) — skips empty
    mode = getattr(req, "validate_mode", "")
    if mode and mode not in (
        models.RuleValidateModeFast,
        models.RuleValidateModeFull,
    ):
        errs["ValidateMode"] = "must be a valid value"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_update_include_rule_tree_request(req) -> str | None:
    """Validate UpdateIncludeRuleTreeRequest.

    Mirrors Go UpdateIncludeRuleTreeRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    if not getattr(req, "include_version", 0):
        errs["IncludeVersion"] = "cannot be blank"

    # Rules: nested validation (Validatable)
    rules = getattr(req, "rules", None)
    if rules is not None:
        r_errs = _rules_errors(rules)
        if r_errs:
            errs["Rules"] = r_errs

    # ValidateMode: In(Fast, Full) — skips empty
    mode = getattr(req, "validate_mode", "")
    if mode and mode not in (
        models.RuleValidateModeFast,
        models.RuleValidateModeFull,
    ):
        errs["ValidateMode"] = "must be a valid value"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — include_versions.go
# =========================================================================


def validate_create_include_version_request(req) -> str | None:
    """Validate CreateIncludeVersionRequest.

    Mirrors Go CreateIncludeVersionRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    if not getattr(req, "create_from_version", 0):
        errs["CreateFromVersion"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_include_version_request(req) -> str | None:
    """Validate GetIncludeVersionRequest.

    Mirrors Go GetIncludeVersionRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    if not getattr(req, "version", 0):
        errs["Version"] = "cannot be blank"
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_list_include_versions_request(req) -> str | None:
    """Validate ListIncludeVersionsRequest.

    Mirrors Go ListIncludeVersionsRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_list_available_criteria_request(req) -> str | None:
    """Validate ListAvailableCriteriaRequest (include).

    Mirrors Go ListAvailableCriteriaRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    if not getattr(req, "version", 0):
        errs["Version"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_list_available_behaviors_request(req) -> str | None:
    """Validate ListAvailableBehaviorsRequest (include).

    Mirrors Go ListAvailableBehaviorsRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.include_id:
        errs["IncludeID"] = "cannot be blank"
    if not getattr(req, "version", 0):
        errs["Version"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — products.go
# =========================================================================


def validate_get_products_request(req) -> str | None:
    """Validate GetProductsRequest. Mirrors Go GetProductsRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — property.go
# =========================================================================


def validate_get_properties_request(req) -> str | None:
    """Validate GetPropertiesRequest. Mirrors Go GetPropertiesRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_create_property_request(req) -> str | None:
    """Validate CreatePropertyRequest.

    Mirrors Go CreatePropertyRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"

    # Property: nested validation (Validatable)
    prop = getattr(req, "property", None)
    if prop is not None:
        p_errs = _property_create_errors(prop)
        if p_errs:
            errs["Property"] = p_errs

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_property_request(req) -> str | None:
    """Validate GetPropertyRequest. Mirrors Go GetPropertyRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_remove_property_request(req) -> str | None:
    """Validate RemovePropertyRequest. Mirrors Go RemovePropertyRequest.Validate()."""
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_map_property_id_to_name_request(req) -> str | None:
    """Validate MapPropertyIDToNameRequest.

    Mirrors Go MapPropertyIDToNameRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_map_property_name_to_id_request(req) -> str | None:
    """Validate MapPropertyNameToIDRequest.

    Mirrors Go MapPropertyNameToIDRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    if not req.name:
        errs["Name"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — property_hostname_activation.go
# =========================================================================


def validate_get_property_hostname_activation_request(req) -> str | None:
    """Validate GetPropertyHostnameActivationRequest.

    Mirrors Go GetPropertyHostnameActivationRequest.Validate().
    """
    errs: dict[str, str | None] = {}

    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"

    # ContractID: Required.When(GroupID != "")
    contract_id = getattr(req, "contract_id", "")
    group_id = getattr(req, "group_id", "")
    if group_id and not contract_id:
        errs["ContractID"] = "cannot be blank when GroupID is provided"
    if contract_id and not group_id:
        errs["GroupID"] = "cannot be blank when ContractID is provided"

    if not req.hostname_activation_id:
        errs["HostnameActivationID"] = "cannot be blank"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_list_property_hostname_activations_request(req) -> str | None:
    """Validate ListPropertyHostnameActivationsRequest.

    Mirrors Go ListPropertyHostnameActivationsRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"

    contract_id = getattr(req, "contract_id", "")
    group_id = getattr(req, "group_id", "")
    if group_id and not contract_id:
        errs["ContractID"] = "cannot be blank when GroupID is provided"
    if contract_id and not group_id:
        errs["GroupID"] = "cannot be blank when ContractID is provided"

    offset = getattr(req, "offset", 0)
    if offset != 0 and offset < 0:
        errs["Offset"] = "must be no less than 0"

    limit = getattr(req, "limit", 0)
    if limit != 0:
        if limit < 1:
            errs["Limit"] = "must be no less than 1"
        elif limit > _MAX_HOSTNAMES_PER_PAGE:
            errs["Limit"] = f"must be no greater than {_MAX_HOSTNAMES_PER_PAGE}"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_cancel_property_hostname_activation_request(req) -> str | None:
    """Validate CancelPropertyHostnameActivationRequest.

    Mirrors Go CancelPropertyHostnameActivationRequest.Validate().
    Note: Go has a known bug where HostnameActivationID validates
    r.PropertyID instead of r.HostnameActivationID — mirrored exactly.
    """
    errs: dict[str, str | None] = {}

    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"

    contract_id = getattr(req, "contract_id", "")
    group_id = getattr(req, "group_id", "")
    if group_id and not contract_id:
        errs["ContractID"] = "cannot be blank when GroupID is provided"
    if contract_id and not group_id:
        errs["GroupID"] = "cannot be blank when ContractID is provided"

    # Go bug: validates r.PropertyID for HostnameActivationID field
    if not req.property_id:
        errs["HostnameActivationID"] = "cannot be blank"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — property_hostname_bucket.go
# =========================================================================


def validate_patch_property_hostname_bucket_request(req) -> str | None:
    """Validate PatchPropertyHostnameBucketRequest.

    Mirrors Go PatchPropertyHostnameBucketRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"

    # Body: Required + Validatable (triggers Body.Validate())
    body = getattr(req, "body", None)
    if body is None:
        errs["Body"] = "cannot be blank"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — propertyhostname.go
# =========================================================================


def validate_get_property_version_hostnames_request(req) -> str | None:
    """Validate GetPropertyVersionHostnamesRequest.

    Mirrors Go GetPropertyVersionHostnamesRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    if not getattr(req, "property_version", 0):
        errs["PropertyVersion"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_update_property_version_hostnames_request(req) -> str | None:
    """Validate UpdatePropertyVersionHostnamesRequest.

    Mirrors Go UpdatePropertyVersionHostnamesRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    if not getattr(req, "property_version", 0):
        errs["PropertyVersion"] = "cannot be blank"

    # Hostnames: nested validation — list of Hostname, each with Validate()
    hostnames = getattr(req, "hostnames", None)
    if hostnames is not None:
        host_errs = _validate_list(hostnames, _hostname_errors)
        if host_errs:
            errs["Hostnames"] = host_errs

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_patch_property_version_hostnames_request(req) -> str | None:
    """Validate PatchPropertyVersionHostnamesRequest.

    Mirrors Go PatchPropertyVersionHostnamesRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    if not getattr(req, "property_version", 0):
        errs["PropertyVersion"] = "cannot be blank"

    body = getattr(req, "body", None)
    if body is None:
        errs["Body"] = "cannot be blank"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_audit_history_request(req) -> str | None:
    """Validate GetAuditHistoryRequest.

    Mirrors Go GetAuditHistoryRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not getattr(req, "hostname", ""):
        errs["Hostname"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — propertyversion.go
# =========================================================================


def validate_get_property_versions_request(req) -> str | None:
    """Validate GetPropertyVersionsRequest.

    Mirrors Go GetPropertyVersionsRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_property_version_request(req) -> str | None:
    """Validate GetPropertyVersionRequest.

    Mirrors Go GetPropertyVersionRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    if not getattr(req, "property_version", 0):
        errs["PropertyVersion"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_create_property_version_request(req) -> str | None:
    """Validate CreatePropertyVersionRequest.

    Mirrors Go CreatePropertyVersionRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"

    # Version: nested validation (Validatable PropertyVersionCreate)
    version = getattr(req, "version", None)
    if version is not None:
        v_errs = _property_version_create_errors(version)
        if v_errs:
            errs["Version"] = v_errs

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_latest_version_request(req) -> str | None:
    """Validate GetLatestVersionRequest.

    Mirrors Go GetLatestVersionRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    # ActivatedOn: In(VersionProduction, VersionStaging) — skips empty
    activated_on = getattr(req, "activated_on", "")
    if activated_on and activated_on not in (
        models.VersionProduction,
        models.VersionStaging,
    ):
        errs["ActivatedOn"] = "must be a valid value"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_available_behaviors_request(req) -> str | None:
    """Validate GetAvailableBehaviorsRequest.

    Mirrors Go GetAvailableBehaviorsRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    if not getattr(req, "property_version", 0):
        errs["PropertyVersion"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_get_available_criteria_request(req) -> str | None:
    """Validate GetAvailableCriteriaRequest.

    Mirrors Go GetAvailableCriteriaRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    if not getattr(req, "property_version", 0):
        errs["PropertyVersion"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_list_available_includes_request(req) -> str | None:
    """Validate ListAvailableIncludesRequest.

    Mirrors Go ListAvailableIncludesRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    if not getattr(req, "property_version", 0):
        errs["PropertyVersion"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_list_referenced_includes_request(req) -> str | None:
    """Validate ListReferencedIncludesRequest.

    Mirrors Go ListReferencedIncludesRequest.Validate().
    """
    errs: dict[str, str | None] = {}
    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    if not getattr(req, "property_version", 0):
        errs["PropertyVersion"] = "cannot be blank"
    if not req.group_id:
        errs["GroupID"] = "cannot be blank"
    if not req.contract_id:
        errs["ContractID"] = "cannot be blank"
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — rule.go
# =========================================================================


def validate_get_rule_tree_request(req) -> str | None:
    """Validate GetRuleTreeRequest.

    Mirrors Go GetRuleTreeRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    if not getattr(req, "property_version", 0):
        errs["PropertyVersion"] = "cannot be blank"

    # ValidateMode: In(Fast, Full) — skips empty
    mode = getattr(req, "validate_mode", "")
    if mode and mode not in (
        models.RuleValidateModeFast,
        models.RuleValidateModeFull,
    ):
        errs["ValidateMode"] = "must be a valid value"

    # RuleFormat: Match(validRuleFormat) — skips empty
    rule_format = getattr(req, "rule_format", "")
    if rule_format and not _VALID_RULE_FORMAT.match(rule_format):
        errs["RuleFormat"] = "must be in a valid format"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def validate_update_rules_request(req) -> str | None:
    """Validate UpdateRulesRequest.

    Mirrors Go UpdateRulesRequest.Validate().
    """
    errs: dict[str, str | dict | None] = {}

    if not req.property_id:
        errs["PropertyID"] = "cannot be blank"
    if not getattr(req, "property_version", 0):
        errs["PropertyVersion"] = "cannot be blank"

    # ValidateMode: In(Fast, Full) — skips empty
    mode = getattr(req, "validate_mode", "")
    if mode and mode not in (
        models.RuleValidateModeFast,
        models.RuleValidateModeFull,
    ):
        errs["ValidateMode"] = "must be a valid value"

    # Rules: nested validation (Validatable RulesUpdate)
    rules = getattr(req, "rules", None)
    if rules is not None:
        r_errs = _rules_update_errors(rules)
        if r_errs:
            errs["Rules"] = r_errs

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


# =========================================================================
# Exported request validators — search.go
# =========================================================================


def validate_search_request(req) -> str | None:
    """Validate SearchRequest.

    Mirrors Go SearchRequest.Validate().
    """
    errs: dict[str, str | None] = {}

    key = getattr(req, "key", "")
    if not key:
        errs["SearchKey"] = "cannot be blank"
    elif key not in (
        models.SearchKeyEdgeHostname,
        models.SearchKeyHostname,
        models.SearchKeyPropertyName,
    ):
        errs["SearchKey"] = "must be a valid value"

    value = getattr(req, "value", "")
    if not value:
        errs["SearchValue"] = "cannot be blank"

    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)
