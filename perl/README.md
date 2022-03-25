# perl module

How to use this Perl module:

```
BEGIN {
    if (!(exists $ENV{'TOOLBOX_HOME'} && -d "$ENV{'TOOLBOX_HOME'}/perl")) {
        print "This script requires libraries that are provided by the toolbox project.\n";
        print "Toolbox can be acquired from https://github.com/perftool-incubator/toolbox and\n";
        print "then use 'export TOOLBOX_HOME=/path/to/toolbox' so that it can be located.\n";
        exit 1;
    }
}
use lib "$ENV{'TOOLBOX_HOME'}/perl";
use toolbox::json;
use toolbox::logging;
use toolbox::cpu;
use toolbox::metrics;
use toolbox::run;
use toolbox::jsonsettings;
```
