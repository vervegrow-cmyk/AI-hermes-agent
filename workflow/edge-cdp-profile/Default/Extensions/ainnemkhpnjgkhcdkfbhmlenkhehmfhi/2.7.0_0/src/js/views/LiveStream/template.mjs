export default `
<section class="col-4 px-0">
	<div class="content-box">
		<div id="livestreamEventsSearchBar">
			<div class="row">
				<div id="livestreamEventsSearchWrapper" class="col-9 border-right border-bottom pr-0">
					<input type="text" class="pl-2" id="livestreamEventsSearch" placeholder="Search events by content">
				</div>
				<div class="col pl-0 d-flex flex-row-reverse">
					<div class="pr-2 pl-1 py-2 d-flex text-secondary searchbar-action" id="livestreamOpenHelp">
						<span class="my-auto">
							<i class="fas fa-fw fa-question"></i>
						</span>
					</div>
					<div class="pl-2 py-2 d-flex text-secondary searchbar-action" id="livestreamClearEvents">
						<span class="my-auto">
							<i class="fas fa-fw fa-trash-alt"></i>
						</span>
					</div>
					<div class="pl-2 py-2 d-flex text-secondary searchbar-action" id="livestreamToggleConsole">
						<span class="my-auto">
							<i class="far fa-fw fa-laptop-code"></i>
						</span>
					</div>
				</div>
			</div>
		</div>
		<div id="livestreamEventsWrapper">
			<ul id="livestreamEvents" class="list-group m-0 no-border-radius">
				<li class="my-auto text-center font-weight-bold text-secondary lead">No events available</li>
			</ul>
		</div>
	</div>
</section>
<section class="col-8 px-0 bc-right">
	<div class="content-box">
		<div id="livestreamDetailWrapper">
			<div id="livestreamDetails" class="card">
				<div class="card-body d-flex text-center font-weight-bold text-secondary lead">
					<p class="my-auto mx-auto">No event selected</p>
				</div>
			</div>
		</div>
	</div>
</section>
`;
