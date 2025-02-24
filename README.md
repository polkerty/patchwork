[[DEMO]](github.com/polkerty/patchwork)

There’s a fascinating mailing list thread going on right now about the issues with Postgres commitfest that I think I could solve. https://www.postgresql.org/message-id/flat/b8a67d6dd34fe5e1b61272d11d40e5f576a00a0a.camel%40j-davis.com#510b3437c7110296960157ebe4e013de.

Here are the key issues that are interesting to me: 
* We don’t know the state of open patches. Are we waiting for the author or for a review? What’s a TL;DR of what needs to be done?
* Reviewers don’t really know what to review. Many open patches are either not ready for a review or not relevant to the reviewer, so it takes a huge amount of work just to find some work.

I imagine a world where 
* Every reviewer is shown a nice queue of patches that are ready for review and relevant to the reviewer’s expertise, as determined perhaps by cross-referencing Git commit history with the files changed in the patch.
* We can coordinate patches across the review pool, such that every patch that IS reviewable is assigned to someone, and we use comparative advantage such that more experienced reviewers see the harder patches. Furthermore, the assignment of patches is transparent: there is a birds-eye of the patches, and we can see how they’re split up.
