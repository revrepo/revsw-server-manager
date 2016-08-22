#!/bin/bash

echo "Running server http tests"

testCommands=(
     "sudo /usr/lib/nagios/plugins/check_http -H rum01.revsw.net -u http://rum01.revsw.net/service -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -H www.victor-gartvich.com -u http://www.victor-gartvich.com/ -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -H www.forgestrategy.com -u http://www.forgestrategy.com/ -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -H cdn.mbeans2.com -u http://cdn.mbeans2.com/images/billboards/Home/main/2015-uppababy-billboard-full.jpg -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -H mbeans.com -u http://mbeans.com/ -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -H www.revsw.com -u http://www.revsw.com/ -e 301"
     "sudo /usr/lib/nagios/plugins/check_http -H cdn.turbonomic.com -u http://cdn.turbonomic.com/wp-content/plugins/wp-views/embedded/res/css/wpv-pagination.css -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -H m.jisusaiche.com -u http://m.jisusaiche.com/js/fz-1.3.6-min.js -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -H cdn.footankleinstitute.com -u http://cdn.footankleinstitute.com/Image/Common/Quote.png -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -H www.revapm.com -u http://www.revapm.com/ -e 301"
     "sudo /usr/lib/nagios/plugins/check_http -H www.revapm.com -u https://www.revapm.com/ --ssl -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -H cdn.footankleinstitute.com -u http://cdn.footankleinstitute.com/images/quotes/Source/AngiesList.png -e 200"
     "sudo /usr/lib/nagios/plugins/check_http -H cdn.golflocker.com -u http://cdn.golflocker.com/images/items/auto/000/01F/0E/inter_i7950.jpg -e 200"
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

