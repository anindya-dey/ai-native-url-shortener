use std::sync::Arc;

use url_shortener::app::build_app;
use url_shortener::store::Store;

#[tokio::main]
async fn main() {
    let base_url = url_shortener::config::base_url_from_env().unwrap_or_else(|err| {
        eprintln!("{err}");
        std::process::exit(1);
    });

    let app = build_app(base_url, Arc::new(Store::new()));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap();
    println!("listening on {}", listener.local_addr().unwrap());
    axum::serve(listener, app).await.unwrap();
}
