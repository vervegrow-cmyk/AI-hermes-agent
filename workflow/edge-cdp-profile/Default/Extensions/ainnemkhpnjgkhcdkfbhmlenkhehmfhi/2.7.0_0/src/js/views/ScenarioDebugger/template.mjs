export default `
<section class="col px-0">
	<div class="content-box">
		<div id="moduleListSearchBar">
			<div class="row">
				<div id="moduleSearchWrapper" class="col-10 border-right border-bottom pr-0">
					<input type="text" class="pl-2" id="moduleSearch" placeholder="Name or ID of the module">
				</div>
				<div class="col pl-0 d-flex flex-row-reverse">
					<div class="pr-2 pl-1 py-2 d-flex text-secondary searchbar-action" id="scenarioDebuggerOpenHelp">
						<span class="my-auto">
							<i class="fas fa-fw fa-question"></i>
						</span>
					</div>
				</div>
			</div>
		</div>
		<div id="moduleList">
			<ul id="moduleListItems" class="list-group m-0 no-border-radius">
				<li class="my-auto text-center font-weight-bold text-secondary lead">No modules available</li>
			</ul>
		</div>
	</div>
</section>
<section class="col px-0 bc-center">
	<div class="content-box">
		<div id="cycleList">
			<ul id="cycleListItems" class="list-group m-0 no-border-radius">
				<li class="my-auto text-center font-weight-bold text-secondary lead">No module selected</li>
			</ul>
		</div>
	</div>
</section>
<section class="col-6 px-0 bc-right">
	<div class="content-box">
		<div id="eventList">
			<ul id="eventListItems" class="list-group m-0 no-border-radius">
				<li class="my-auto text-center font-weight-bold text-secondary lead">No operation selected</li>
			</ul>
		</div>
	</div>
</section>
`;
