from __future__ import annotations

import argparse
import json

import bootstrap
from src.modules.shopify_listing.runners.publish_vendor_catalog import publish_vendor_catalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a vendor catalog to selected Shopify channels.")
    parser.add_argument("--vendor", default="Doba", help="Vendor name to scan and publish.")
    parser.add_argument(
        "--channels",
        nargs="*",
        default=["Online Store", "Shop", "Pinterest", "Facebook & Instagram"],
        help="Target Shopify publication names.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/audits/vendor-catalog-publish-report.json",
        help="Path for the JSON audit report.",
    )
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="Stop immediately when a category update or publish step fails for a product.",
    )
    parser.add_argument(
        "--max-products",
        type=int,
        default=1,
        help="Maximum number of products to publish in this run. Use 1 for true one-by-one release.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore any existing report and start scanning from the beginning again.",
    )
    parser.add_argument(
        "--include-fully-published",
        action="store_true",
        help="Do not skip products that are already published to all selected channels.",
    )
    args = parser.parse_args()

    result = publish_vendor_catalog(
        vendor=args.vendor,
        publication_names=args.channels,
        report_path=args.report_path,
        stop_on_failure=args.stop_on_failure,
        max_products=args.max_products,
        resume_from_report=not args.no_resume,
        skip_fully_published=not args.include_fully_published,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
