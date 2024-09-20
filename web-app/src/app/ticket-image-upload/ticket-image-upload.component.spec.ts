import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TicketImageUploadComponent } from './ticket-image-upload.component';

describe('TicketImageUploadComponent', () => {
  let component: TicketImageUploadComponent;
  let fixture: ComponentFixture<TicketImageUploadComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TicketImageUploadComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TicketImageUploadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
