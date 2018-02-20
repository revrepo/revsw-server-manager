#!/bin/bash

echo "Running server http tests"

testCommands=(
     "sudo /usr/lib/nagios/plugins/check_http -I localhost -u http://rum01.revsw.net/service -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -I localhost -u http://www.victor-gartvich.com/ -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -I localhost -u http://www.forgestrategy.com/ -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -I localhost -u http://cdn.mbeans2.com/images/billboards/Home/main/2015-uppababy-billboard-full.jpg -e 301"
     "sudo /usr/lib/nagios/plugins/check_http -I localhost -u http://mbeans.com/ -e 301"
     "sudo /usr/lib/nagios/plugins/check_http -I localhost -u http://www.revsw.com/ -e 301"
     "sudo /usr/lib/nagios/plugins/check_http -I localhost -u http://cdn.turbonomic.com/wp-content/plugins/wp-views/embedded/res/css/wpv-pagination.css -e 302"
     "sudo /usr/lib/nagios/plugins/check_http -I localhost -u http://cdn.footankleinstitute.com/Image/Common/Quote.png -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -I localhost -u http://www.revapm.com/ -e 301"
     "sudo /usr/lib/nagios/plugins/check_http -I localhost -u https://www.revapm.com/ --ssl -e 301"
     "sudo /usr/lib/nagios/plugins/check_http -I localhost -u http://cdn.footankleinstitute.com/images/quotes/Source/AngiesList.png -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -I localhost -u http://cdn.golflocker.com/images/items/auto/000/01F/0E/inter_i7950.jpg -e 200"
   )

for (( i = 0; i < ${#testCommands[@]} ; i++ )); do
    printf "\nTest command: ${testCommands[$i]} \n"

    RESULT=`${testCommands[$i]}`

    if [ -n "$RESULT" ]; then
        echo "$RESULT"
        if echo "$RESULT" | grep -q "CRITICAL"
        then
            exit 1
        fi
    fi
done

exit 0
