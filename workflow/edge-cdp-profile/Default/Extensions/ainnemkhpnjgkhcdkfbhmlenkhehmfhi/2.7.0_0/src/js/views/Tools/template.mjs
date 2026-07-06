export default `
<section class="col-8 px-0">
	<div class="content-box">
		<div id="toolsSearchBar">
			<div class="row">
				<div class="col-7 border-right pr-0">
					<input type="text" class="pl-2" id="toolsSearch" placeholder="Search for a tool by name">
				</div>
				<div class="col d-flex flex-row-reverse">
					<div class="pr-2 pl-1 py-2 d-flex text-secondary searchbar-action" id="toolsOpenHelp">
						<span class="my-auto">
							<i class="fas fa-fw fa-question"></i>
						</span>
					</div>
				</div>
			</div>
		</div>
		<div id="toolsWrapper">
			<div id="toolsRow" class="row m-0 p-2">
			</div>
		</div>
	</div>
</section>
<section class="col px-0 bc-right">
	<div class="content-box">
		<div id="toolWindow">
			<div class="fullheight d-flex text-center font-weight-bold text-secondary lead">
				<p class="my-auto mx-auto">No tool selected</p>
			</div>
		</div>
	</div>
</section>
`;
