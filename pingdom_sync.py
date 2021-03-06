import pingdom
import settings

def primary_account_login():
    return pingdom.Pingdom(
        username=settings.PRIMARY_USERNAME,
        password=settings.PRIMARY_PASSWORD,
        appkey=settings.PRIMARY_APPKEY
    )

def secondary_account_login():
    return pingdom.Pingdom(
        username=settings.SECONDARY_USERNAME,
        password=settings.SECONDARY_PASSWORD,
        appkey=settings.SECONDARY_APPKEY
    )

def _action_all(conn, action):
    checks = conn.method('checks')
    for check in checks['checks']:
        print "%s '%s'" % (action, check['name'])
        getattr(conn, action)(check['name']) 

def pause_all(conn):
    _action_all(conn, "pause_check")

def unpause_all(conn):
    _action_all(conn, "unpause_check")

def sync_pingdom_accounts():
    """synchronizes the two pingdom accounts by adding new checks to the 2nd
    account"""
    p = primary_account_login()

    #get primary account checks and save their names/ids
    main_checks = p.method('checks')
    main_checks = {
        check['name']: check['id'] for check in main_checks['checks']
    }

    #get primary account contacts
    main_contacts = p.method('contacts')
    main_contacts = {
        contact['email']: {'name': contact['name'], 'id': contact['id']} \
        for contact in main_contacts['contacts']
    }

    print ">    Checks and contacts retrieved"

    p = secondary_account_login()

    #get 2nd account checks
    secondary_checks = p.method('checks')
    secondary_checks = {
        check['name'][:len(check['name']) - 16]: check['id'] \
        for check in secondary_checks['checks']
    }

    for check, check_id in main_checks.iteritems():
        if check not in secondary_checks and str(check_id) not in settings.IGNORES:
            #get the details
            p = primary_account_login()
            details = p.method('checks/%s' % (main_checks[check],))
            details = {details[d]['name']: details[d] for d in details}

            #put those details in the new check
            p = secondary_account_login()
            check_type = details[check]['type'].keys()[0]
            new_check = p.method(
                url='checks',
                method="POST",
                parameters={
                    'name': "%s [Response Time]" % (check,),
                    'type': 'httpcustom',
                    'host': settings.DEPLOY_SERVER,
                    'url': '/response/%s' % (details[check]['id'],),
                    'port': settings.DEPLOY_PORT,
                    'resolution': details[check]['resolution'],
                    'sendtoemail': details[check]['sendtoemail'],
                    'sendtosms': details[check]['sendtosms'],
                    'sendtotwitter': details[check]['sendtotwitter'],
                    'sendtoiphone': details[check]['sendtoiphone'],
                    'sendnotificationwhendown': details[check]['sendnotificationwhendown'],
                    'notifyagainevery': details[check]['notifyagainevery'],
                    'notifywhenbackup': details[check]['notifywhenbackup'],
                    #for some reason, contactids yields a bad request
                    #'contactids': ''.join([str(main_contacts[a]['id']) + ',' for a in main_contacts])
                }
            )
            print ">    Created new check '%s [Response Time]'" % (check,)

    #get 2nd account contacts
    secondary_contacts = p.method('contacts')
    secondary_contacts = {
        contact['email']: contact['name'] \
        for contact in secondary_contacts['contacts']
    }

    for contact in main_contacts:
        if contact not in secondary_contacts:
            #add the contact to the 2nd account
            new_contact = p.method(
                url='contacts',
                method="POST",
                parameters={
                    'name': main_contacts[contact]['name'],
                    'email': contact,
                }
            )
            print ">    Created new contact '%s'" % (contact,)

    print (">    All checks and contacts synchronized")


if __name__ == '__main__':
    sync_pingdom_accounts()
