// Emit the reviewed native-injection paths from the v1.175.0 Cobra tree.
// Run this file against commit 776faec72dd6e13556f37340f068fd76b16ad575.
package main

import (
	"fmt"
	"github.com/digitalocean/doctl/commands"
	"github.com/spf13/cobra"
	"sort"
	"strings"
)

func main() {
	roots := strings.Fields("1-click account apps auth balance billing-history compute databases dedicated-inference gradient invoice kubernetes monitoring network nfs projects registries registry secrets security serverless-inference spaces vector-databases vpcs")
	allowed := map[string]bool{}
	for _, root := range roots {
		allowed[root] = true
	}
	var lines []string
	var walk func(*cobra.Command, []string, []string)
	walk = func(cmd *cobra.Command, path, aliasPath []string) {
		for _, child := range cmd.Commands() {
			p := append(append([]string{}, path...), child.Name())
			a := append(append([]string{}, aliasPath...), strings.Join(append([]string{child.Name()}, child.Aliases...), "|"))
			canonical := strings.Join(p, " ")
			excluded := canonical == "auth list" || canonical == "auth remove" || canonical == "auth switch" || canonical == "apps spec validate" || strings.HasPrefix(canonical, "apps dev ") || strings.HasPrefix(canonical, "compute plugin ")
			if child.Runnable() && allowed[p[0]] && !excluded {
				lines = append(lines, strings.Join(a, " "))
			}
			walk(child, p, a)
		}
	}
	walk(commands.DoitCmd.Command, nil, nil)
	sort.Strings(lines)
	for _, line := range lines {
		fmt.Println(line)
	}
}
