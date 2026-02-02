"""
ECS Field Mapper - Transforms raw Windows event data to ECS format
This allows rules written in ECS format to work with raw Windows event logs
"""
import logging

logger = logging.getLogger(__name__)

class ECSFieldMapper:
    """Maps raw Windows event fields to ECS (Elastic Common Schema) format"""
    
    # Field mapping from raw Windows event data to ECS
    FIELD_MAPPINGS = {
        # User fields
        'user.name': ['winlog.event_data.TargetUserName', 'winlog.event_data.SubjectUserName', 'winlog.user.name'],
        'user.domain': ['winlog.event_data.TargetDomainName', 'winlog.event_data.SubjectDomainName', 'winlog.user.domain'],
        'user.id': ['winlog.event_data.TargetUserSid', 'winlog.event_data.SubjectUserSid'],
        'user.target.name': ['winlog.event_data.TargetUserName'],
        'user.target.domain': ['winlog.event_data.TargetDomainName'],
        'user.target.id': ['winlog.event_data.TargetUserSid'],
        'user.subject.name': ['winlog.event_data.SubjectUserName'],
        'user.subject.domain': ['winlog.event_data.SubjectDomainName'],
        'user.subject.id': ['winlog.event_data.SubjectUserSid'],
        
        # Group fields
        'group.name': ['winlog.event_data.Group', 'winlog.event_data.MemberName', 'winlog.event_data.TargetUserName'],
        'group.id': ['winlog.event_data.MemberSid'],
        
        # Source fields 
        'source.ip': ['winlog.event_data.IpAddress', 'winlog.event_data.SourceAddress'],
        'source.address': ['winlog.event_data.WorkstationName', 'winlog.event_data.Workstation'],
        'source.domain': ['winlog.event_data.SourceNetworkAddress'],
        'source.port': ['winlog.event_data.SourcePort'],
        
        # Process fields
        'process.name': ['winlog.event_data.NewProcessName', 'winlog.event_data.ProcessName', 'winlog.event_data.Image'],
        'process.executable': ['winlog.event_data.NewProcessName', 'winlog.event_data.ProcessName'],
        'process.command_line': ['winlog.event_data.CommandLine'],
        'process.parent.name': ['winlog.event_data.ParentProcessName', 'winlog.event_data.ParentImage'],
        'process.parent.command_line': ['winlog.event_data.ParentCommandLine'],
        'process.pid': ['winlog.event_data.ProcessId', 'winlog.event_data.NewProcessId'],
        'process.parent.pid': ['winlog.event_data.ParentProcessId'],
        'process.target.name': ['winlog.event_data.TargetImage'],
        'process.working_directory': ['winlog.event_data.CurrentDirectory'],
        
        # Authentication/Logon fields
        'event.category': ['event.category'],  # Already ECS
        'event.outcome': ['event.outcome'],  # Already ECS
        'event.action': ['event.action'],  # Already ECS
        'event.code': ['event.code'],  # Already ECS
        
        # Logon specific
        'winlog.logon.type': ['winlog.event_data.LogonType'],
        'winlog.logon.authentication_package': ['winlog.event_data.AuthenticationPackageName'],
        'winlog.logon.logon_process': ['winlog.event_data.LogonProcessName'],
        'winlog.logon.id': ['winlog.event_data.TargetLogonId', 'winlog.event_data.LogonId'],
        
        # File fields
        'file.path': ['winlog.event_data.TargetFilename', 'winlog.event_data.FileName'],
        'file.name': ['winlog.event_data.FileName'],
        'file.directory': ['winlog.event_data.TargetFilename'],
        
        # Registry fields
        'registry.path': ['winlog.event_data.TargetObject'],
        'registry.key': ['winlog.event_data.TargetObject'],
        'registry.value': ['winlog.event_data.Details'],
        
        # Network fields
        'destination.ip': ['winlog.event_data.DestAddress', 'winlog.event_data.DestinationIp'],
        'destination.port': ['winlog.event_data.DestPort', 'winlog.event_data.DestinationPort'],
        'network.protocol': ['winlog.event_data.Protocol'],
        
        # Service fields
        'service.name': ['winlog.event_data.ServiceName'],
        'service.type': ['winlog.event_data.ServiceType'],
        
        # DNS fields
        'dns.question.name': ['winlog.event_data.QueryName'],
        'dns.question.type': ['winlog.event_data.QueryType'],
    }
    
    @classmethod
    def transform_query(cls, query):
        """
        Transform an ES|QL query with ECS field names to use actual Windows event field names
        
        Args:
            query: ES|QL query string with ECS field names
            
        Returns:
            Transformed query with Windows event field names
        """
        transformed = query
        
        # Replace ECS fields with actual field names (use first mapping)
        for ecs_field, raw_fields in cls.FIELD_MAPPINGS.items():
            if ecs_field in transformed:
                # Use the first available field as primary mapping
                primary_field = raw_fields[0]
                
                # Replace exact matches (with word boundaries)
                import re
                # Match field name but not as part of another word
                pattern = r'\b' + re.escape(ecs_field) + r'\b'
                transformed = re.sub(pattern, primary_field, transformed)
        
        return transformed
    
    @classmethod
    def get_coalesce_expression(cls, ecs_field):
        """
        Get a COALESCE expression to try multiple raw field mappings
        
        Args:
            ecs_field: ECS field name
            
        Returns:
            COALESCE expression string, or the first field if only one mapping
        """
        raw_fields = cls.FIELD_MAPPINGS.get(ecs_field, [ecs_field])
        
        if len(raw_fields) == 1:
            return raw_fields[0]
        
        # Create COALESCE expression
        fields_str = ', '.join(raw_fields)
        return f'COALESCE({fields_str})'
    
    @classmethod
    def transform_query_with_coalesce(cls, query):
        """
        Transform query using COALESCE for fields with multiple mappings
        This provides fallback if primary field doesn't exist
        
        Args:
            query: ES|QL query with ECS fields
            
        Returns:
            Transformed query with COALESCE expressions
        """
        transformed = query
        
        import re
        
        # Replace ECS fields with COALESCE expressions where applicable
        for ecs_field, raw_fields in cls.FIELD_MAPPINGS.items():
            if ecs_field in transformed and len(raw_fields) > 1:
                pattern = r'\b' + re.escape(ecs_field) + r'\b'
                coalesce_expr = cls.get_coalesce_expression(ecs_field)
                transformed = re.sub(pattern, coalesce_expr, transformed)
        
        return transformed
    
    @classmethod
    def get_available_mappings(cls):
        """Return all available ECS -> Raw field mappings"""
        return cls.FIELD_MAPPINGS.copy()
    
    @classmethod
    def add_custom_mapping(cls, ecs_field, raw_fields):
        """
        Add a custom field mapping
        
        Args:
            ecs_field: ECS field name
            raw_fields: List of raw field names (or single string)
        """
        if isinstance(raw_fields, str):
            raw_fields = [raw_fields]
        cls.FIELD_MAPPINGS[ecs_field] = raw_fields
        logger.info(f"Added custom mapping: {ecs_field} -> {raw_fields}")
