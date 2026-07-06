import { entityKind } from "../../entity.js";
import { applyMixins } from "../../utils.js";
import { SQL, sql } from "../../sql/sql.js";
import { QueryPromise } from "../../query-promise.js";

//#region src/mysql-core/query-builders/count.ts
var MySqlCountBuilder = class MySqlCountBuilder extends SQL {
	static [entityKind] = "MySqlCountBuilder";
	dialect;
	session;
	static buildEmbeddedCount(source, filters, parens) {
		const query = sql`select count(*) from ${source}${sql` where ${filters}`.if(filters)}`;
		return parens ? sql`(${query})` : query;
	}
	constructor(countConfig) {
		super(MySqlCountBuilder.buildEmbeddedCount(countConfig.source, countConfig.filters, true).queryChunks);
		this.countConfig = countConfig;
		this.dialect = countConfig.dialect;
		this.session = countConfig.session;
		this.mapWith((e) => {
			if (typeof e === "number") return e;
			return Number(e ?? 0);
		});
	}
	build() {
		const { filters, source } = this.countConfig;
		const query = MySqlCountBuilder.buildEmbeddedCount(source, filters);
		return this.dialect.sqlToQuery(query);
	}
	execute(placeholderValues) {
		return this.session.prepareQuery(this.build(), "arrays", (rows) => {
			const v = rows[0]?.[0];
			if (typeof v === "number") return v;
			return v ? Number(v) : 0;
		}).execute(placeholderValues);
	}
};
applyMixins(MySqlCountBuilder, [QueryPromise]);

//#endregion
export { MySqlCountBuilder };
//# sourceMappingURL=count.js.map