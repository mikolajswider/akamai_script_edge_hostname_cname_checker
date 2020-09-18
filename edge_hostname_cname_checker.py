#!/usr/bin/python3
import json
import dns.resolver
import time
import requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from urllib.parse import urljoin
import re

"""
The edge_hostname_cname_checker.py script finds all property hostnames CNAMEd to an input Edge Hostname, within a Customer Account. The script uses edgegrid for python and dnspython libraries. There are four inputs: the Edge Hostname, the Account Switchkey, the .edgerc File Path and finally the Section Name containing your API credentials.
Contributors:
Miko (mswider@akamai.com) as Chief Programmer
edge_hostname_cname_checker.py v1.0
"""

def get_properties(contractId, groupId, path, section, switchkey):
    # setting up authentication as in https://github.com/akamai/AkamaiOPEN-edgegrid-python
    dict_list=[]
    edgerc = EdgeRc(path)
    baseurl = 'https://%s' % edgerc.get(section, "host")
    http_request = requests.Session()
    http_request.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    # setting up request headers
    headers ={}
    headers['PAPI-Use-Prefixes']="true"
    http_request.headers = headers
    # getting the latest property version: https://developer.akamai.com/api/core_features/property_manager/v1.html#getproperties
    http_response = http_request.get(urljoin(baseurl, '/papi/v1/properties?contractId='+contractId+'&groupId='+groupId+'&accountSwitchKey='+switchkey))
    http_status_code= http_response.status_code
    http_content = json.loads(http_response.text)
    for item in http_content['properties']['items']:
        dict_list = dict_list + [{"latestVersion": item['latestVersion'], "propertyId": item['propertyId'], "contractId":contractId, "groupId": groupId}]
    return (dict_list)
# Not needed...
def get_latest_property_version(propertyId, contractId, groupId, path, section, switchkey):
    # setting up authentication as in https://github.com/akamai/AkamaiOPEN-edgegrid-python
    edgerc = EdgeRc(path)
    baseurl = 'https://%s' % edgerc.get(section, "host")
    http_request = requests.Session()
    http_request.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    # setting up request headers
    headers ={}
    headers['PAPI-Use-Prefixes']="true"
    http_request.headers = headers
    # getting the latest property version: https://developer.akamai.com/api/core_features/property_manager/v1.html#getlatestversion
    http_response = http_request.get(urljoin(baseurl, '/papi/v1/properties/'+propertyId+'/versions/latest?activatedOn=PRODUCTION&contractId='+contractId+'&groupId='+groupId+'&accountSwitchKey='+switchkey))
    http_status_code= http_response.status_code
    http_content = json.loads(http_response.text)
    version = re.search('(.*)\/versions\/(\d*)?(.*)',http_content).group(2)
    return (version)
def get_property_hostnames(latestVersion, propertyId, contractId, groupId, path, section, switchkey):
    # setting up authentication as in https://github.com/akamai/AkamaiOPEN-edgegrid-python
    property_hostnames_list=[]
    edgerc = EdgeRc(path)
    baseurl = 'https://%s' % edgerc.get(section, "host")
    http_request = requests.Session()
    http_request.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    # setting up request headers
    headers ={}
    headers['PAPI-Use-Prefixes']="true"
    http_request.headers = headers
    # getting the list of groups and contracts assosciated to groups: https://developer.akamai.com/api/core_features/property_manager/v1.html#getgroups
    http_response = http_request.get(urljoin(baseurl, '/papi/v1/properties/'+propertyId+'/versions/'+str(latestVersion)+'/hostnames?contractId='+contractId+'&groupId='+groupId+'&validateHostnames=false&accountSwitchKey='+switchkey))
    http_status_code= http_response.status_code
    http_content = json.loads(http_response.text)
    for item in http_content['hostnames']['items']:
        property_hostnames_list=property_hostnames_list+[item['cnameFrom']]
    return(property_hostnames_list)
def main():
    print("\nThe edge_hostname_cname_checker.py script finds all property hostnames CNAMEd to an input edge hostname, within a Customer Account. The script uses edgegrid for python and dnspython libraries.")
    print("There are four inputs: the Edge Hostname, the Account Switchkey, the .edgerc File Path and finally the Section Name containing your API credentials.")
    print("Contributors:")
    print("Miko (mswider) as Chief Programmer")
    print("edge_hostname_cname_checker.py v1.0")
    # defining variables
    dict_list = []
    property_hostnames_list = []
    answer_list = []
    nb_groups = 0
    nb_contracts = 0
    nb_properties = 0
    nb_hostnames = 0
    warning = False
    nx_domain_list=[]
    unknown_list=[]
    timeout_list=[]
    # defining inputs
    edge_hostname = input("\nProvide the Edge Hostname: ")
    switchkey = input("\nProvide the customer's Account ID: ")
    path = input("\nProvide the location of  your .edgerc file: ")
    section = input("\nProvide the section name of your .edgerc file containing your API credentials: ")
    # setting up authentication as in https://github.com/akamai/AkamaiOPEN-edgegrid-python
    edgerc = EdgeRc(path)
    baseurl = 'https://%s' % edgerc.get(section, "host")
    http_request = requests.Session()
    http_request.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    # setting up request headers
    headers ={}
    headers['PAPI-Use-Prefixes']="true"
    http_request.headers = headers
    print('\nGetting the list of all groups and all assosciated contracts...')
    #https://developer.akamai.com/api/core_features/property_manager/v1.html#getgroups
    http_response = http_request.get(urljoin(baseurl, '/papi/v1/groups?accountSwitchKey='+switchkey))
    http_status_code= http_response.status_code
    http_content= json.loads(http_response.text)
    #print(http_content)
    print('Getting the list of all properties...')
    for item in http_content['groups']['items']:
        nb_groups = nb_groups + 1
        for contractId in item['contractIds']:
            nb_contracts = nb_contracts + 1
            dict_list = dict_list + get_properties(contractId, item['groupId'], path, section, switchkey)
    nb_properties = len(dict_list)
    print('There are '+str(nb_groups)+' groups, '+str(nb_contracts)+ ' contracts and '+str(nb_properties)+' properties in the '+switchkey+' account.')
    print('\nGetting the list of all property hostnames...')
    for bloc in dict_list:
        property_hostnames_list = property_hostnames_list + get_property_hostnames(bloc['latestVersion'], bloc['propertyId'], bloc['contractId'], bloc['groupId'], path, section, switchkey)
    nb_hostnames = len(property_hostnames_list)
    print('There are '+str(nb_hostnames)+' property hostnames in the '+switchkey+' account.')
    print('\nProceeding with DNS (CNAME record) resolution of all property hostnames...')
    for hostname in property_hostnames_list:
        try:
            output = (dns.resolver.query(hostname,'CNAME', raise_on_no_answer=False))
        except dns.exception.Timeout:
            warning = True
            timeout_list = timeout_list + [hostname]
        except dns.rdatatype.UnknownRdatatype:
            warning = True
            unknown_list = unknown_list + [hostname]
        except dns.resolver.NXDOMAIN:
            warning = True
            nx_domain_list = nx_domain_list + [hostname]
        else:
            if edge_hostname in str(output.rrset):
                answer_list =  answer_list + [hostname]
    # Displaying hostnames for which DNS resolution failed
    if timeout_list != []:
        print('The DNS resolution failed with the exception dns.exception.Timeout for:')
        print(*timeout_list, sep = "\n")
    if unknown_list != []:
        print('The DNS resolution failed with the exception dns.rdatatype.UnknownRdatatype for:')
        print(*unknown_list, sep = "\n")
    if nx_domain_list != []:
        print('The DNS resolution failed with the exception dns.resolver.NXDOMAIN for:')
        print(*nx_domain_list, sep = "\n")
    # Displaying final answers
    if warning:
        if answer_list == []:
            print("\nThe DNS (CNAME record) resolution was not successfull for the records printed above. Appart from these, there are no property hostnames CNAMEd to " + str(edge_hostname)+".")
            print("\n")
        else:
            print("\nThe DNS (CNAME record) resolution was not successfull for the records printed above. Appart from these, the following property hostname(s) is/are CNAMEd to " + str(edge_hostname) + ":")
            print(*answer_list, sep = "\n")
            print("\n")
    else:
        if answer_list == []:
            print("There are no property hostnames CNAMEd to " + str(edge_hostname)+".")
            print("\n")
        else:
            print("The following property hostname(s) is/are CNAMEd to " + str(edge_hostname) + ":")
            print(*answer_list, sep = "\n")
            print("\n")
if __name__ == '__main__':
    main()
